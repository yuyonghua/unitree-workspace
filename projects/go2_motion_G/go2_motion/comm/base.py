"""
通信抽象基类。

定义与机器人通信的统一接口，使上层控制逻辑
可以在仿真和真机之间无缝切换。
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np

from .robot_state import RobotState, MotorCmd


class CommInterface(ABC):
    """
    机器人通信接口抽象基类。
    
    所有通信后端 (DDS仿真、DDS真机) 必须实现此接口。
    电机索引使用 **模型顺序** (FL, FR, RL, RR)，
    具体到 SDK 电机顺序的映射在实现类内部完成。
    """

    @abstractmethod
    def init(self) -> None:
        """初始化通信通道"""
        pass

    @abstractmethod
    def get_state(self) -> RobotState:
        """
        获取当前机器人状态。
        
        Returns:
            RobotState: 当前状态 (关节角度、IMU等)，
                        关节数据已转换为模型顺序。
        """
        pass

    @abstractmethod
    def send_motor_cmds(self, cmds: List[MotorCmd]) -> None:
        """
        发送电机控制指令。
        
        Args:
            cmds: 12 个电机指令，按模型关节顺序排列。
                  实现类负责映射到 SDK 电机顺序。
        """
        pass

    @abstractmethod
    def send_position_cmd(
        self,
        target_q: np.ndarray,
        kps: np.ndarray,
        kds: np.ndarray,
        target_dq: np.ndarray = None,
        tau_ff: np.ndarray = None,
    ) -> None:
        """
        发送位置控制指令 (便捷方法)。
        
        Args:
            target_q: 目标关节角度 [12], 模型顺序
            kps: 位置增益 [12]
            kds: 速度增益 [12]
            target_dq: 目标关节速度 [12], 默认为零
            tau_ff: 前馈力矩 [12], 默认为零
        """
        pass

    @abstractmethod
    def send_damping_cmd(self, kd: float = 8.0) -> None:
        """发送阻尼指令 (安全模式)"""
        pass

    @abstractmethod
    def send_zero_cmd(self) -> None:
        """发送零力矩指令"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否已连接到机器人/仿真器"""
        pass

    @abstractmethod
    def wait_for_connection(self, timeout: float = 10.0) -> bool:
        """
        等待连接建立。
        
        Args:
            timeout: 超时时间 (秒)
            
        Returns:
            是否成功连接
        """
        pass
