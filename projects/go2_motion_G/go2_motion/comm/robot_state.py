"""
机器人状态数据结构 - 与 SDK IDL 解耦的中间表示。

将 unitree_sdk2py 的 LowState_ IDL 消息转换为纯 numpy 数据结构，
使上层控制逻辑不依赖具体的 DDS IDL 类型。
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class MotorCmd:
    """单个电机控制指令"""
    q: float = 0.0       # 目标位置 (rad)
    dq: float = 0.0      # 目标速度 (rad/s)
    kp: float = 0.0      # 位置增益
    kd: float = 0.0      # 速度增益
    tau: float = 0.0     # 前馈力矩 (Nm)


@dataclass
class RobotState:
    """
    机器人状态数据类。
    
    从 LowState_ 中提取关键信息，存储为 numpy 数组。
    所有数据按 **模型关节顺序** 排列 (FL, FR, RL, RR)，
    与 SDK 电机顺序的映射由 JointMapping 处理。
    """
    # 电机状态 (12 个关节)
    motor_q: np.ndarray = field(default_factory=lambda: np.zeros(12, dtype=np.float32))
    motor_dq: np.ndarray = field(default_factory=lambda: np.zeros(12, dtype=np.float32))
    motor_tau: np.ndarray = field(default_factory=lambda: np.zeros(12, dtype=np.float32))

    # IMU 状态
    imu_quaternion: np.ndarray = field(
        default_factory=lambda: np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    )  # [w, x, y, z]
    imu_gyroscope: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    imu_accelerometer: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))

    # 遥控器原始数据
    wireless_remote: bytes = field(default_factory=lambda: bytes(40))

    # 时间戳
    tick: int = 0

    def is_valid(self) -> bool:
        """检查状态是否有效 (已收到至少一次数据)"""
        return self.tick > 0
