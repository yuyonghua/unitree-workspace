import numpy as np
from go2_motion.config import Go2Config
from go2_motion.policy.base_policy import BasePolicy

class StandPolicy(BasePolicy):
    """
    内置站立策略（PD）。
    不依赖神经网络模型，直接输出 action=0，配合后续逻辑会使用 default_angles。
    也可以加入平滑插值逻辑，但在高级 API 中一般在循环里完成插值。
    """
    def __init__(self, config: Go2Config):
        self.config = config

    def compute_action(self, obs: np.ndarray) -> np.ndarray:
        """
        全零动作，使目标关节回到 default_angles。
        """
        return np.zeros(self.config.num_actions, dtype=np.float32)
