"""
DDS 通信实现 - 基于 unitree_sdk2py。

通过 CycloneDDS 与 MuJoCo 仿真器或真机通信。
仿真器使用 loopback + domain_id=1，
真机使用物理网卡 + domain_id=0。

关键注意事项 (来自官方 example/python/stand_go2.py):
  1. CRC 校验始终需要 (仿真器也会校验)
  2. 控制频率 500Hz (dt=0.002s)，不是 50Hz
  3. head/level_flag/mode 等协议字段必须设置
"""

import time
import numpy as np
from typing import List
import threading

from unitree_sdk2py.core.channel import (
    ChannelFactoryInitialize,
    ChannelPublisher,
    ChannelSubscriber,
)
from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC

from .base import CommInterface
from .robot_state import RobotState, MotorCmd
from ..control.joint_mapping import JointMapping


# DDS Topics
TOPIC_LOWCMD = "rt/lowcmd"
TOPIC_LOWSTATE = "rt/lowstate"


class DDSComm(CommInterface):
    """
    基于 unitree_sdk2py DDS 的通信实现。
    
    支持仿真 (domain_id=1, interface="lo") 和
    真机 (domain_id=0, interface="eth0") 两种模式。
    
    Args:
        config: Go2Config 配置对象
    """

    def __init__(self, config):
        self.config = config
        self.joint_mapping = JointMapping(config.joint2motor_idx)

        self._low_cmd = unitree_go_msg_dds__LowCmd_()
        self._robot_state = RobotState()
        self._state_lock = threading.Lock()
        self._crc = CRC()

        self._lowcmd_pub = None
        self._lowstate_sub = None
        self._connected = False
        self._recv_count = 0

    def init(self) -> None:
        """初始化 DDS 通信通道"""
        ChannelFactoryInitialize(self.config.domain_id, self.config.interface)

        self._lowcmd_pub = ChannelPublisher(TOPIC_LOWCMD, LowCmd_)
        self._lowcmd_pub.Init()

        self._lowstate_sub = ChannelSubscriber(TOPIC_LOWSTATE, LowState_)
        self._lowstate_sub.Init(self._lowstate_handler, 10)

        # 初始化命令结构 (包含协议字段 + CRC)
        self._init_cmd()

        print(
            f"[DDSComm] Initialized: domain_id={self.config.domain_id}, "
            f"interface={self.config.interface}"
        )

    def _init_cmd(self) -> None:
        """
        初始化 LowCmd 结构。
        
        参考官方 example/python/stand_go2.py:
        - head, level_flag, gpio 必须设置
        - motor_cmd[i].mode = 0x01 (PMSM 模式)  
        - CRC 每次发送前计算
        """
        self._low_cmd.head[0] = 0xFE
        self._low_cmd.head[1] = 0xEF
        self._low_cmd.level_flag = 0xFF
        self._low_cmd.gpio = 0

        for i in range(20):  # Go2 IDL 有 20 个 motor_cmd 槽位
            self._low_cmd.motor_cmd[i].mode = 0x01  # PMSM 模式
            self._low_cmd.motor_cmd[i].q = 0.0
            self._low_cmd.motor_cmd[i].kp = 0.0
            self._low_cmd.motor_cmd[i].dq = 0.0
            self._low_cmd.motor_cmd[i].kd = 0.0
            self._low_cmd.motor_cmd[i].tau = 0.0

    def _lowstate_handler(self, msg: LowState_) -> None:
        """
        DDS LowState 回调 (在 DDS 接收线程中执行)。
        
        立即将数据从 DDS 消息中拷贝出来，避免生命周期问题。
        """
        with self._state_lock:
            self._recv_count += 1

            # 提取电机状态，从 SDK 电机顺序映射到模型关节顺序
            for model_idx in range(12):
                motor_idx = self.joint_mapping.model_to_motor(model_idx)
                self._robot_state.motor_q[model_idx] = float(msg.motor_state[motor_idx].q)
                self._robot_state.motor_dq[model_idx] = float(msg.motor_state[motor_idx].dq)
                self._robot_state.motor_tau[model_idx] = float(msg.motor_state[motor_idx].tau_est)

            # IMU 状态
            for i in range(4):
                self._robot_state.imu_quaternion[i] = float(msg.imu_state.quaternion[i])
            for i in range(3):
                self._robot_state.imu_gyroscope[i] = float(msg.imu_state.gyroscope[i])
                self._robot_state.imu_accelerometer[i] = float(msg.imu_state.accelerometer[i])

            # 遥控器原始数据
            self._robot_state.wireless_remote = bytes(msg.wireless_remote)

            # tick
            self._robot_state.tick = self._recv_count

            if not self._connected:
                self._connected = True
                print(f"[DDSComm] First state received, motor_q={self._robot_state.motor_q[:3].round(4)}")

    def get_state(self) -> RobotState:
        """获取当前机器人状态的快照 (深拷贝)。"""
        with self._state_lock:
            if not self._connected:
                return RobotState()

            state = RobotState()
            state.motor_q = self._robot_state.motor_q.copy()
            state.motor_dq = self._robot_state.motor_dq.copy()
            state.motor_tau = self._robot_state.motor_tau.copy()
            state.imu_quaternion = self._robot_state.imu_quaternion.copy()
            state.imu_gyroscope = self._robot_state.imu_gyroscope.copy()
            state.imu_accelerometer = self._robot_state.imu_accelerometer.copy()
            state.wireless_remote = self._robot_state.wireless_remote
            state.tick = self._robot_state.tick
            return state

    def send_motor_cmds(self, cmds: List[MotorCmd]) -> None:
        """发送电机控制指令 (按模型关节顺序)。"""
        assert len(cmds) == 12, f"Expected 12 motor commands, got {len(cmds)}"

        for model_idx in range(12):
            motor_idx = self.joint_mapping.model_to_motor(model_idx)
            self._low_cmd.motor_cmd[motor_idx].q = float(cmds[model_idx].q)
            self._low_cmd.motor_cmd[motor_idx].dq = float(cmds[model_idx].dq)
            self._low_cmd.motor_cmd[motor_idx].kp = float(cmds[model_idx].kp)
            self._low_cmd.motor_cmd[motor_idx].kd = float(cmds[model_idx].kd)
            self._low_cmd.motor_cmd[motor_idx].tau = float(cmds[model_idx].tau)

        self._publish_cmd()

    def send_position_cmd(
        self,
        target_q: np.ndarray,
        kps: np.ndarray,
        kds: np.ndarray,
        target_dq: np.ndarray = None,
        tau_ff: np.ndarray = None,
    ) -> None:
        """
        发送位置控制指令。
        
        MuJoCo bridge LowCmdHandler 计算:
          ctrl[i] = tau + kp * (q - sensor_q) + kd * (dq - sensor_dq)
        """
        if target_dq is None:
            target_dq = np.zeros(12, dtype=np.float32)
        if tau_ff is None:
            tau_ff = np.zeros(12, dtype=np.float32)

        for model_idx in range(12):
            motor_idx = self.joint_mapping.model_to_motor(model_idx)
            self._low_cmd.motor_cmd[motor_idx].q = float(target_q[model_idx])
            self._low_cmd.motor_cmd[motor_idx].dq = float(target_dq[model_idx])
            self._low_cmd.motor_cmd[motor_idx].kp = float(kps[model_idx])
            self._low_cmd.motor_cmd[motor_idx].kd = float(kds[model_idx])
            self._low_cmd.motor_cmd[motor_idx].tau = float(tau_ff[model_idx])

        self._publish_cmd()

    def send_damping_cmd(self, kd: float = 8.0) -> None:
        """发送阻尼指令 - 所有关节进入阻尼模式"""
        for i in range(12):
            motor_idx = self.joint_mapping.model_to_motor(i)
            self._low_cmd.motor_cmd[motor_idx].q = 0.0
            self._low_cmd.motor_cmd[motor_idx].dq = 0.0
            self._low_cmd.motor_cmd[motor_idx].kp = 0.0
            self._low_cmd.motor_cmd[motor_idx].kd = kd
            self._low_cmd.motor_cmd[motor_idx].tau = 0.0

        self._publish_cmd()

    def send_zero_cmd(self) -> None:
        """发送零力矩指令"""
        for i in range(12):
            motor_idx = self.joint_mapping.model_to_motor(i)
            self._low_cmd.motor_cmd[motor_idx].q = 0.0
            self._low_cmd.motor_cmd[motor_idx].dq = 0.0
            self._low_cmd.motor_cmd[motor_idx].kp = 0.0
            self._low_cmd.motor_cmd[motor_idx].kd = 0.0
            self._low_cmd.motor_cmd[motor_idx].tau = 0.0

        self._publish_cmd()

    def is_connected(self) -> bool:
        return self._connected

    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """等待连接建立 (收到第一个 LowState)。"""
        start = time.time()
        while not self._connected:
            if time.time() - start > timeout:
                print(f"[DDSComm] Connection timeout after {timeout}s")
                return False
            time.sleep(0.01)

        print(f"[DDSComm] Successfully connected (recv_count={self._recv_count}).")
        return True

    def _publish_cmd(self) -> None:
        """发布 LowCmd (始终带 CRC 校验)"""
        self._low_cmd.crc = self._crc.Crc(self._low_cmd)
        self._lowcmd_pub.Write(self._low_cmd)
