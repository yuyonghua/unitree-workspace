"""
关节索引映射器。

处理 RL 模型关节顺序和 SDK 电机顺序之间的映射。

RL 模型关节顺序 (MuJoCo / Isaac Gym):
  FL_hip, FL_thigh, FL_calf,  (0, 1, 2)
  FR_hip, FR_thigh, FR_calf,  (3, 4, 5)
  RL_hip, RL_thigh, RL_calf,  (6, 7, 8)
  RR_hip, RR_thigh, RR_calf   (9, 10, 11)

Go2 SDK 电机顺序 (motor_state / motor_cmd):
  FR_hip, FR_thigh, FR_calf,  (0, 1, 2)
  FL_hip, FL_thigh, FL_calf,  (3, 4, 5)
  RR_hip, RR_thigh, RR_calf,  (6, 7, 8)
  RL_hip, RL_thigh, RL_calf   (9, 10, 11)

映射关系 (model → motor):
  joint2motor_idx = [3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]
  即: model[0]=FL_hip → motor[3], model[3]=FR_hip → motor[0], ...
"""

from typing import List


# 预定义的关节名称
GO2_MODEL_JOINT_NAMES = [
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
]

GO2_SDK_MOTOR_NAMES = [
    "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
    "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
    "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
    "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
]

# 仿真模式: MuJoCo 中关节顺序与模型一致，直接映射
SIM_JOINT2MOTOR_IDX = list(range(12))  # [0, 1, 2, ..., 11]

# 真机模式: 模型关节 → SDK 电机索引
REAL_JOINT2MOTOR_IDX = [3, 4, 5, 0, 1, 2, 9, 10, 11, 6, 7, 8]


class JointMapping:
    """
    关节索引映射器。
    
    在模型关节顺序和 SDK 电机顺序之间互转。
    
    Args:
        joint2motor_idx: 模型关节索引 → SDK 电机索引的映射表。
                         仿真用 [0..11]，真机用 [3,4,5,0,1,2,9,10,11,6,7,8]。
    """

    def __init__(self, joint2motor_idx: List[int] = None):
        if joint2motor_idx is None:
            joint2motor_idx = SIM_JOINT2MOTOR_IDX
        
        self._joint2motor = list(joint2motor_idx)
        
        # 构建反向映射: motor_idx → model_idx
        self._motor2joint = [0] * 12
        for model_idx, motor_idx in enumerate(self._joint2motor):
            self._motor2joint[motor_idx] = model_idx

    def model_to_motor(self, model_idx: int) -> int:
        """模型关节索引 → SDK 电机索引"""
        return self._joint2motor[model_idx]

    def motor_to_model(self, motor_idx: int) -> int:
        """SDK 电机索引 → 模型关节索引"""
        return self._motor2joint[motor_idx]

    @property
    def joint2motor_idx(self) -> List[int]:
        """获取映射表"""
        return self._joint2motor.copy()

    @property
    def motor2joint_idx(self) -> List[int]:
        """获取反向映射表"""
        return self._motor2joint.copy()
