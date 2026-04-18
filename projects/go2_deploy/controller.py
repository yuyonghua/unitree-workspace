"""
Go2 RL 控制器核心模块。

直接对齐 go2_rl_gym/deploy/deploy_real/deploy_real_go2.py 的逻辑,
但整合了仿真和真机的双模支持。

核心原则:
  1. 单线程控制循环 (避免线程调度的延迟抖动)
  2. 观测构建、重力投影、动作缩放 100% 复刻原项目
  3. 安全状态机: ZERO_TORQUE → STAND → RL_WALK → DAMPING
  4. 每次退出都必须发送阻尼指令
"""

import time
import struct
import numpy as np
import torch
import yaml

from unitree_sdk2py.core.channel import (
    ChannelFactoryInitialize,
    ChannelPublisher,
    ChannelSubscriber,
)
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_ as LowCmdType
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_ as LowStateType
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC


# ============================================================
# 辅助函数 (完全复刻 go2_rl_gym 的实现)
# ============================================================

def get_gravity_orientation(quaternion):
    """
    从四元数 [w,x,y,z] 计算机体坐标系下的重力投影向量。
    公式来源: go2_rl_gym/deploy/deploy_mujoco/deploy_go2.py
    """
    qw, qx, qy, qz = quaternion[0], quaternion[1], quaternion[2], quaternion[3]
    gx = 2 * (-qz * qx + qw * qy)
    gy = -2 * (qz * qy + qw * qx)
    gz = 1 - 2 * (qw * qw + qz * qz)
    return np.array([gx, gy, gz], dtype=np.float32)


# ============================================================
# 配置加载
# ============================================================

class Config:
    """从 YAML 加载配置, 与 go2_rl_gym 的 config 格式兼容"""

    def __init__(self, yaml_path: str):
        with open(yaml_path, "r") as f:
            cfg = yaml.load(f, Loader=yaml.FullLoader)

        self.policy_path = cfg["policy_path"]
        self.domain_id = cfg.get("domain_id", 1)
        self.interface = cfg.get("interface", "lo")
        self.lowcmd_topic = cfg.get("lowcmd_topic", "rt/lowcmd")
        self.lowstate_topic = cfg.get("lowstate_topic", "rt/lowstate")

        self.control_dt = cfg["control_dt"]
        self.joint2motor_idx = cfg["joint2motor_idx"]

        self.kps = np.array(cfg["kps"], dtype=np.float32)
        self.kds = np.array(cfg["kds"], dtype=np.float32)
        self.default_angles = np.array(cfg["default_angles"], dtype=np.float32)
        self.liedown_angles = np.array(cfg["liedown_angles"], dtype=np.float32)

        self.standup_kp = cfg.get("standup_kp", 40.0)
        self.standup_kd = cfg.get("standup_kd", 0.6)
        self.standup_time = cfg.get("standup_time", 2.0)

        self.ang_vel_scale = cfg["ang_vel_scale"]
        self.dof_pos_scale = cfg["dof_pos_scale"]
        self.dof_vel_scale = cfg["dof_vel_scale"]
        self.action_scale = cfg["action_scale"]
        self.cmd_scale = np.array(cfg["cmd_scale"], dtype=np.float32)
        self.max_cmd = np.array(cfg["max_cmd"], dtype=np.float32)

        self.num_actions = cfg["num_actions"]
        self.num_obs = cfg["num_obs"]


# ============================================================
# 遥控器解析 (复刻 go2_rl_gym 的 RemoteController)
# ============================================================

class KeyMap:
    R1 = 0; L1 = 1; start = 2; select = 3
    R2 = 4; L2 = 5; F1 = 6; F2 = 7
    A = 8; B = 9; X = 10; Y = 11
    up = 12; right = 13; down = 14; left = 15


class RemoteController:
    """解析 LowState 中 wireless_remote 的 40 字节数据"""

    def __init__(self):
        self.lx = 0.0
        self.ly = 0.0
        self.rx = 0.0
        self.ry = 0.0
        self.button = [0] * 16

    def set(self, data: bytes):
        if len(data) < 24:
            return
        keys = struct.unpack("H", data[2:4])[0]
        for i in range(16):
            self.button[i] = (keys & (1 << i)) >> i
        self.lx = struct.unpack("f", data[4:8])[0]
        self.rx = struct.unpack("f", data[8:12])[0]
        self.ry = struct.unpack("f", data[12:16])[0]
        self.ly = struct.unpack("f", data[20:24])[0]


# ============================================================
# 核心控制器
# ============================================================

class Go2Controller:
    """
    Go2 RL 控制器。

    集成了 DDS 通信、RL 推理、安全状态机。
    支持键盘和遥控器两种输入源。

    状态机:
      IDLE → (等待连接) → ZERO_TORQUE → (按键触发) → STANDING
      STANDING → (按键触发) → RL_WALKING
      RL_WALKING → (按键触发) → STANDING
      任何状态 → (退出) → LIEDOWN → DAMPING
    """

    def __init__(self, config: Config):
        self.config = config
        self.crc = CRC()
        self.remote = RemoteController()

        # ---- DDS ----
        self.low_cmd = unitree_go_msg_dds__LowCmd_()
        self.low_state = None
        self._state_received = False

        # ---- RL Policy ----
        self.policy = torch.jit.load(config.policy_path, map_location="cpu")
        self.policy.eval()
        self._warm_up_policy()

        # ---- 状态变量 (全部预分配, 避免运行时内存分配) ----
        self.obs = np.zeros(config.num_obs, dtype=np.float32)
        self.action = np.zeros(config.num_actions, dtype=np.float32)
        self.qj = np.zeros(config.num_actions, dtype=np.float32)
        self.dqj = np.zeros(config.num_actions, dtype=np.float32)
        self.cmd = np.zeros(3, dtype=np.float32)
        self.target_dof_pos = config.default_angles.copy()

    def init_dds(self):
        """初始化 DDS 通道"""
        ChannelFactoryInitialize(self.config.domain_id, self.config.interface)

        self.lowcmd_pub = ChannelPublisher(self.config.lowcmd_topic, LowCmdType)
        self.lowcmd_pub.Init()

        self.lowstate_sub = ChannelSubscriber(self.config.lowstate_topic, LowStateType)
        self.lowstate_sub.Init(self._on_low_state, 10)

        self._init_cmd()
        print(f"[DDS] Initialized: domain_id={self.config.domain_id}, interface={self.config.interface}")

    def wait_for_connection(self, timeout: float = 15.0):
        """阻塞等待直到收到第一帧 LowState"""
        print("[DDS] Waiting for robot/simulator connection...")
        t0 = time.time()
        while not self._state_received:
            if time.time() - t0 > timeout:
                raise RuntimeError(f"Connection timeout after {timeout}s. Is the simulator/robot running?")
            time.sleep(0.01)
        print("[DDS] Connected successfully.")

    # ---- 状态机动作 (每个都是阻塞式, 单线程安全) ----

    def send_zero_torque(self, duration: float = 0.5):
        """零力矩状态 - 机器人自由落体/瘫软"""
        print("[State] Zero torque...")
        steps = int(duration / self.config.control_dt)
        for _ in range(steps):
            for i in range(20):
                self.low_cmd.motor_cmd[i].q = 0.0
                self.low_cmd.motor_cmd[i].dq = 0.0
                self.low_cmd.motor_cmd[i].kp = 0.0
                self.low_cmd.motor_cmd[i].kd = 0.0
                self.low_cmd.motor_cmd[i].tau = 0.0
            self._send_cmd()
            time.sleep(self.config.control_dt)

    def move_to_pos(self, target_angles: np.ndarray, duration: float = None,
                    kp: float = None, kd: float = None):
        """
        平滑过渡到目标关节角度。
        从当前实际位置线性插值到目标位置, 避免突变。

        这是站立和趴下的核心函数。
        """
        if duration is None:
            duration = self.config.standup_time
        if kp is None:
            kp = self.config.standup_kp
        if kd is None:
            kd = self.config.standup_kd

        num_steps = int(duration / self.config.control_dt)
        dof_idx = self.config.joint2motor_idx

        # 读取当前真实关节位置 (从最新的 low_state)
        init_pos = np.zeros(12, dtype=np.float32)
        if self.low_state is not None:
            for i in range(12):
                init_pos[i] = self.low_state.motor_state[dof_idx[i]].q
        else:
            init_pos = target_angles.copy()

        for step in range(num_steps):
            alpha = step / num_steps
            for j in range(12):
                motor_idx = dof_idx[j]
                pos = init_pos[j] * (1 - alpha) + target_angles[j] * alpha
                self.low_cmd.motor_cmd[motor_idx].q = float(pos)
                self.low_cmd.motor_cmd[motor_idx].dq = 0.0
                self.low_cmd.motor_cmd[motor_idx].kp = kp
                self.low_cmd.motor_cmd[motor_idx].kd = kd
                self.low_cmd.motor_cmd[motor_idx].tau = 0.0
            self._send_cmd()
            time.sleep(self.config.control_dt)

    def stand_up(self):
        """站立: 从当前姿态平滑过渡到默认站立角度"""
        print("[State] Standing up...")
        self.move_to_pos(self.config.default_angles)
        print("[State] Stand complete.")

    def lie_down(self):
        """趴下: 从当前姿态平滑过渡到趴下角度"""
        print("[State] Lying down...")
        self.move_to_pos(self.config.liedown_angles, duration=2.0)
        print("[State] Lie down complete.")

    def hold_stand(self):
        """
        维持站立姿态 (不使用 RL, 纯 PD 保持)。
        适合在等待用户切换到行走模式时持续调用。
        """
        dof_idx = self.config.joint2motor_idx
        for i in range(12):
            motor_idx = dof_idx[i]
            self.low_cmd.motor_cmd[motor_idx].q = float(self.config.default_angles[i])
            self.low_cmd.motor_cmd[motor_idx].dq = 0.0
            self.low_cmd.motor_cmd[motor_idx].kp = self.config.standup_kp
            self.low_cmd.motor_cmd[motor_idx].kd = self.config.standup_kd
            self.low_cmd.motor_cmd[motor_idx].tau = 0.0
        self._send_cmd()

    def rl_step(self):
        """
        执行一步 RL 推理并发送控制指令。

        100% 复刻 go2_rl_gym/deploy/deploy_real/deploy_real_go2.py 的 run() 方法。
        """
        if self.low_state is None:
            return

        dof_idx = self.config.joint2motor_idx

        # 1. 读取关节状态 (SDK电机顺序 → 模型顺序)
        for i in range(12):
            self.qj[i] = self.low_state.motor_state[dof_idx[i]].q
            self.dqj[i] = self.low_state.motor_state[dof_idx[i]].dq

        # 2. IMU 数据
        ang_vel = np.array(
            [self.low_state.imu_state.gyroscope], dtype=np.float32
        ) * self.config.ang_vel_scale
        quat = self.low_state.imu_state.quaternion
        gravity = get_gravity_orientation(quat)

        # 3. 构建观测 (与原项目一模一样的排列)
        qj_obs = (self.qj - self.config.default_angles) * self.config.dof_pos_scale
        dqj_obs = self.dqj * self.config.dof_vel_scale

        self.obs[:3] = ang_vel
        self.obs[3:6] = gravity
        self.obs[6:9] = self.cmd * self.config.cmd_scale
        self.obs[9:21] = qj_obs
        self.obs[21:33] = dqj_obs
        self.obs[33:45] = self.action

        # 4. RL 推理
        obs_tensor = torch.from_numpy(self.obs).unsqueeze(0)
        with torch.inference_mode():
            result = self.policy(obs_tensor)
            if isinstance(result, tuple):
                self.action = result[0].squeeze().numpy()
            else:
                self.action = result.squeeze().numpy()

        # 5. 计算目标角度并下发
        self.target_dof_pos = self.config.default_angles + self.action * self.config.action_scale

        for i in range(12):
            motor_idx = dof_idx[i]
            self.low_cmd.motor_cmd[motor_idx].q = float(self.target_dof_pos[i])
            self.low_cmd.motor_cmd[motor_idx].dq = 0.0
            self.low_cmd.motor_cmd[motor_idx].kp = float(self.config.kps[i])
            self.low_cmd.motor_cmd[motor_idx].kd = float(self.config.kds[i])
            self.low_cmd.motor_cmd[motor_idx].tau = 0.0

        self._send_cmd()

    def send_damping(self):
        """发送阻尼指令 - 安全终止状态"""
        for i in range(20):
            self.low_cmd.motor_cmd[i].q = 0.0
            self.low_cmd.motor_cmd[i].dq = 0.0
            self.low_cmd.motor_cmd[i].kp = 0.0
            self.low_cmd.motor_cmd[i].kd = 8.0
            self.low_cmd.motor_cmd[i].tau = 0.0
        self._send_cmd()
        print("[State] Damping sent.")

    def set_cmd(self, vx: float, vy: float, vyaw: float):
        """设置速度指令 (会被 max_cmd 裁剪)"""
        self.cmd[0] = np.clip(vx, -self.config.max_cmd[0], self.config.max_cmd[0])
        self.cmd[1] = np.clip(vy, -self.config.max_cmd[1], self.config.max_cmd[1])
        self.cmd[2] = np.clip(vyaw, -self.config.max_cmd[2], self.config.max_cmd[2])

    # ---- 内部方法 ----

    def _warm_up_policy(self):
        """预热策略网络, 避免首次推理延迟"""
        dummy = torch.zeros((1, self.config.num_obs), dtype=torch.float32)
        with torch.inference_mode():
            for _ in range(10):
                self.policy(dummy)
        print("[Policy] Warm-up complete.")

    def _init_cmd(self):
        """
        初始化 LowCmd 结构。
        mode=0x0A 是真机必须的 (仿真器也兼容)。
        """
        self.low_cmd.head[0] = 0xFE
        self.low_cmd.head[1] = 0xEF
        self.low_cmd.level_flag = 0xFF
        self.low_cmd.gpio = 0
        for i in range(20):
            self.low_cmd.motor_cmd[i].mode = 0x0A
            self.low_cmd.motor_cmd[i].q = 2.146e9   # PosStopF
            self.low_cmd.motor_cmd[i].dq = 16000.0   # VelStopF
            self.low_cmd.motor_cmd[i].kp = 0.0
            self.low_cmd.motor_cmd[i].kd = 0.0
            self.low_cmd.motor_cmd[i].tau = 0.0

    def _on_low_state(self, msg):
        """DDS 回调: 直接保存引用 (单线程消费, 无需深拷贝)"""
        self.low_state = msg
        self.remote.set(self.low_state.wireless_remote)
        if not self._state_received:
            self._state_received = True

    def _send_cmd(self):
        """发布 LowCmd (始终带 CRC)"""
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_pub.Write(self.low_cmd)
