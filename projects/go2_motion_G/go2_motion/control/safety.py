"""
安全管理器。

提供电机控制的安全保障:
- 力矩限制裁剪
- 关节角度限位检查
- 安全启动/停止流程
- 阻尼/零力矩模式
"""

import numpy as np
from typing import List

from ..comm.robot_state import MotorCmd


# Go2 关节限位 (rad) - 保守值
GO2_JOINT_LIMITS = {
    # (lower, upper) for each joint type
    "hip": (-1.047, 1.047),      # ±60°
    "thigh": (-0.663, 2.966),    # ~-38° to 170°
    "calf": (-2.721, -0.837),    # ~-156° to -48°
}

# Go2 关节顺序: hip, thigh, calf × 4 legs
GO2_JOINT_TYPES = ["hip", "thigh", "calf"] * 4

# 最大力矩限制 (Nm)
GO2_MAX_TORQUE = 23.7  # Go2 电机最大力矩


class SafetyManager:
    """
    安全管理器 - 确保电机指令在安全范围内。
    
    Args:
        config: Go2Config 配置对象
    """

    def __init__(self, config):
        self.config = config
        self.max_torque = GO2_MAX_TORQUE
        self._build_limits()

    def _build_limits(self):
        """构建关节限位数组"""
        self.joint_lower = np.zeros(12, dtype=np.float32)
        self.joint_upper = np.zeros(12, dtype=np.float32)

        for i, jtype in enumerate(GO2_JOINT_TYPES):
            low, high = GO2_JOINT_LIMITS[jtype]
            self.joint_lower[i] = low
            self.joint_upper[i] = high

    def clip_target_position(self, target_q: np.ndarray) -> np.ndarray:
        """
        裁剪目标位置到关节限位内。
        
        Args:
            target_q: 目标关节角度 [12]
            
        Returns:
            裁剪后的关节角度 [12]
        """
        return np.clip(target_q, self.joint_lower, self.joint_upper)

    def clip_torque(self, torque: np.ndarray) -> np.ndarray:
        """
        裁剪力矩到安全范围内。
        
        Args:
            torque: 力矩 [12]
            
        Returns:
            裁剪后的力矩 [12]
        """
        return np.clip(torque, -self.max_torque, self.max_torque)

    def check_position_safe(self, target_q: np.ndarray) -> bool:
        """
        检查目标位置是否在安全范围内。
        
        Args:
            target_q: 目标关节角度 [12]
            
        Returns:
            是否安全
        """
        return bool(
            np.all(target_q >= self.joint_lower)
            and np.all(target_q <= self.joint_upper)
        )

    def check_kp_safe(self, kps: np.ndarray, max_kp: float = 50.0) -> bool:
        """
        检查 PD 增益是否在安全范围内。
        
        Args:
            kps: 位置增益 [12]
            max_kp: 最大允许 kp
            
        Returns:
            是否安全
        """
        return bool(np.all(kps <= max_kp) and np.all(kps >= 0))
