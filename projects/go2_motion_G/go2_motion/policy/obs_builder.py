import numpy as np

from go2_motion.config import Go2Config
from go2_motion.comm.robot_state import RobotState

class ObsBuilder:
    """
    Observation 构建器，为 RL 模型准备输入状态。
    """
    def __init__(self, config: Go2Config):
        self.config = config

    def _get_gravity_orientation(self, quaternion: np.ndarray) -> np.ndarray:
        """
        从四元数计算机体坐标系下的重力向量 (不依赖 scipy)。
        四元数格式为 [w, x, y, z] (SDK 默认)。
        返回 [3] 的重力分量投影 (相当于世界系的 [0,0,-1] 在机体系的表示)。
        """
        w, x, y, z = quaternion
        
        gx = -2.0 * (x * z - w * y)
        gy = -2.0 * (y * z + w * x)
        gz = -(w * w - x * x - y * y + z * z)
        
        return np.array([gx, gy, gz], dtype=np.float32)

    def build(self, state: RobotState, cmd: np.ndarray, last_action: np.ndarray) -> np.ndarray:
        """
        构建 45 维观测向量。
        
        Args:
            state: 当前机器人状态 (模型关节顺序)
            cmd: 用户命令 [vx, vy, vyaw]
            last_action: 上一次策略输出动作 [12]
        
        Returns:
            obs: 45 维一维 numpy 数组
        """
        obs = np.zeros(self.config.num_obs, dtype=np.float32)

        # 0:3 - 角速度 (ang_vel * ang_vel_scale)
        obs[0:3] = state.imu_gyroscope * self.config.ang_vel_scale

        # 3:6 - 投影重力
        obs[3:6] = self._get_gravity_orientation(state.imu_quaternion)

        # 6:9 - 用户指令 (cmd * cmd_scale)
        # 我们还可以根据 config.max_cmd 来截断? (这里交给外部控制，或简单裁剪)
        clipped_cmd = np.clip(cmd, -self.config.max_cmd, self.config.max_cmd)
        obs[6:9] = clipped_cmd * self.config.cmd_scale

        # 9:21 - 关节位置差值 ((q - default_q) * dof_pos_scale)
        q_error = state.motor_q - self.config.default_angles
        obs[9:21] = q_error * self.config.dof_pos_scale

        # 21:33 - 关节速度 (dq * dof_vel_scale)
        obs[21:33] = state.motor_dq * self.config.dof_vel_scale

        # 33:45 - 上一次动作
        obs[33:45] = last_action

        return obs
