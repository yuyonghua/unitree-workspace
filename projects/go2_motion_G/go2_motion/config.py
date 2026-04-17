"""
统一配置管理。

从 YAML 文件加载配置，支持仿真和真机两种模式。
配置项与 go2_rl_gym 的 deploy 配置格式兼容。
"""

import os
import numpy as np
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Go2Config:
    """Go2 运动控制配置"""

    # ---- 运行模式 ----
    mode: str = "sim"                    # "sim" 或 "real"

    # ---- DDS 通信 ----
    domain_id: int = 1                   # 仿真=1, 真机=0
    interface: str = "lo"                # 仿真="lo", 真机="eth0" 等
    use_crc: bool = False                # 真机需要 CRC 校验
    lowcmd_topic: str = "rt/lowcmd"
    lowstate_topic: str = "rt/lowstate"

    # ---- 控制参数 ----
    control_dt: float = 0.02             # 控制周期 (s), 50Hz
    kps: np.ndarray = field(default_factory=lambda: np.full(12, 20.0, dtype=np.float32))
    kds: np.ndarray = field(default_factory=lambda: np.full(12, 0.5, dtype=np.float32))
    default_angles: np.ndarray = field(default_factory=lambda: np.array([
        0.1,  0.8,  -1.5,   # FL: hip, thigh, calf
       -0.1,  0.8,  -1.5,   # FR
        0.1,  1.0,  -1.5,   # RL
       -0.1,  1.0,  -1.5,   # RR
    ], dtype=np.float32))

    # ---- 关节映射 ----
    # 仿真中 MuJoCo 关节顺序与模型一致 → [0..11]
    # 真机中 SDK 电机顺序不同 → [3,4,5,0,1,2,9,10,11,6,7,8]
    joint2motor_idx: List[int] = field(default_factory=lambda: list(range(12)))

    # ---- RL 策略参数 ----
    policy_path: str = ""                # .pt 模型路径
    num_obs: int = 45                    # observation 维度
    num_actions: int = 12                # action 维度

    # Observation 缩放因子
    ang_vel_scale: float = 0.25
    dof_pos_scale: float = 1.0
    dof_vel_scale: float = 0.05
    action_scale: float = 0.25

    # Command 缩放因子 和 最大值
    cmd_scale: np.ndarray = field(default_factory=lambda: np.array([2.0, 2.0, 0.25], dtype=np.float32))
    max_cmd: np.ndarray = field(default_factory=lambda: np.array([2.0, 1.0, 2.5], dtype=np.float32))

    # ---- 安全启动参数 (真机) ----
    standup_time: float = 2.0            # 站立过渡时间 (s)

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Go2Config":
        """从 YAML 文件加载配置"""
        with open(yaml_path, "r") as f:
            data = yaml.load(f, Loader=yaml.FullLoader)

        config = cls()

        # 运行模式
        config.mode = data.get("mode", "sim")

        # DDS 通信
        config.domain_id = data.get("domain_id", 1 if config.mode == "sim" else 0)
        config.interface = data.get("interface", "lo" if config.mode == "sim" else "eth0")
        config.use_crc = data.get("use_crc", config.mode == "real")
        config.lowcmd_topic = data.get("lowcmd_topic", "rt/lowcmd")
        config.lowstate_topic = data.get("lowstate_topic", "rt/lowstate")

        # 控制参数
        config.control_dt = data.get("control_dt", 0.02)
        if "kps" in data:
            config.kps = np.array(data["kps"], dtype=np.float32)
        if "kds" in data:
            config.kds = np.array(data["kds"], dtype=np.float32)
        if "default_angles" in data:
            config.default_angles = np.array(data["default_angles"], dtype=np.float32)

        # 关节映射
        if "joint2motor_idx" in data:
            config.joint2motor_idx = data["joint2motor_idx"]

        # RL 策略
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(yaml_path)))
        if "policy_path" in data:
            path = data["policy_path"]
            path = path.replace("{PROJECT_ROOT}", project_root)
            config.policy_path = path
        config.num_obs = data.get("num_obs", 45)
        config.num_actions = data.get("num_actions", 12)

        # Observation 缩放
        config.ang_vel_scale = data.get("ang_vel_scale", 0.25)
        config.dof_pos_scale = data.get("dof_pos_scale", 1.0)
        config.dof_vel_scale = data.get("dof_vel_scale", 0.05)
        config.action_scale = data.get("action_scale", 0.25)

        if "cmd_scale" in data:
            config.cmd_scale = np.array(data["cmd_scale"], dtype=np.float32)
        if "max_cmd" in data:
            config.max_cmd = np.array(data["max_cmd"], dtype=np.float32)

        # 安全参数
        config.standup_time = data.get("standup_time", 2.0)

        return config

    def __repr__(self):
        return (
            f"Go2Config(mode={self.mode}, domain_id={self.domain_id}, "
            f"interface={self.interface}, control_dt={self.control_dt}, "
            f"policy_path={self.policy_path})"
        )
