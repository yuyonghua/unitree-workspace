import torch
import numpy as np
from go2_motion.config import Go2Config
from go2_motion.policy.base_policy import BasePolicy

class RLPolicy(BasePolicy):
    """
    预训练 RL 模型策略包装器。
    
    加载导出好的 TorchScript (.pt) 模型进行推理计算。
    支持返回单一 tensor，或者 (action, (weights, latent)) 这样带有辅助状态的结构（针对 MoE 模型）。
    """
    def __init__(self, config: Go2Config):
        self.config = config
        self.device = torch.device('cpu')  # 推理统一在 CPU 跑
        self.model = torch.jit.load(config.policy_path, map_location=self.device)
        self.model.eval()
        
        # 预热模型（编译第一遍图，避免运行时首次耗时过长）
        self._warm_up()
        
    def _warm_up(self):
        """预热，消除首次推理抖动"""
        dummy_obs = torch.zeros(
            (1, self.config.num_obs), dtype=torch.float32, device=self.device
        )
        with torch.no_grad():
            for _ in range(5):
                self.model(dummy_obs)

    def compute_action(self, obs: np.ndarray) -> np.ndarray:
        """
        根据观测进行前向传播推理。
        
        Args:
            obs: [45]维一维数组
            
        Returns:
            action: [12]维动作数组
        """
        # 转为 batch size = 1 的 tensor
        obs_tensor = torch.from_numpy(obs).unsqueeze(0).to(self.device).float()
        
        with torch.inference_mode():
            result = self.model(obs_tensor)
            
            # 支持 MoE 或其他返回多个值的情况 (如: go2_moe_...pt 返回 tuple)
            if isinstance(result, tuple):
                action_tensor = result[0]
            else:
                action_tensor = result
                
        # 转换为 1D numpy array
        return action_tensor.squeeze(0).cpu().numpy()
