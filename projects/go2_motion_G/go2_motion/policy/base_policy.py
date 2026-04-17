"""
策略基类。
"""
from abc import ABC, abstractmethod
import numpy as np

class BasePolicy(ABC):
    """
    策略抽象基类。
    """
    @abstractmethod
    def compute_action(self, obs: np.ndarray) -> np.ndarray:
        """
        根据当前观测计算下一次动作。
        
        Args:
            obs: 状态观测数组
            
        Returns:
            action: 控制动作
        """
        pass
