"""
PD 位置控制器。

实现标准的 PD 位置控制:
  τ = kp × (q_target - q_current) + kd × (dq_target - dq_current)

这与 MuJoCo 仿真器中 UnitreeSdk2Bridge.LowCmdHandler 的逻辑一致，
也与真机 Go2 的底层电机驱动器的行为一致。
"""

import numpy as np


def pd_control(
    target_q: np.ndarray,
    current_q: np.ndarray,
    kp: np.ndarray,
    target_dq: np.ndarray,
    current_dq: np.ndarray,
    kd: np.ndarray,
) -> np.ndarray:
    """
    计算 PD 控制力矩。
    
    Args:
        target_q: 目标关节角度 [N]
        current_q: 当前关节角度 [N]
        kp: 位置增益 [N]
        target_dq: 目标关节速度 [N]
        current_dq: 当前关节速度 [N]
        kd: 速度增益 [N]
        
    Returns:
        力矩 [N]
    """
    return (target_q - current_q) * kp + (target_dq - current_dq) * kd


def interpolate_position(
    start_q: np.ndarray,
    target_q: np.ndarray,
    alpha: float,
) -> np.ndarray:
    """
    线性插值关节位置 (用于平滑过渡)。
    
    Args:
        start_q: 起始位置 [N]
        target_q: 目标位置 [N]
        alpha: 插值系数 [0, 1]
        
    Returns:
        插值后的位置 [N]
    """
    alpha = np.clip(alpha, 0.0, 1.0)
    return start_q * (1.0 - alpha) + target_q * alpha
