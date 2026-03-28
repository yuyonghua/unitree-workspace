"""Configuration for Go2/G1 MuJoCo simulation with Vuer visualization."""

from pathlib import Path
from dataclasses import dataclass, field

# Workspace paths
WORKSPACE_ROOT = Path(__file__).parent.parent.parent
MUJOCO_ROBOTS_DIR = WORKSPACE_ROOT / "git/official/unitree_mujoco/unitree_robots"


@dataclass
class RobotConfig:
    """Robot configuration."""
    name: str
    mjcf_file: str
    scene_file: str
    assets_dir: str
    num_joints: int
    joint_names: list[str]
    motor_names: list[str]
    domain_id: int = 1  # Different from real robot (0)
    interface: str = "lo"  # Local loopback for simulation


# Go2 configuration
GO2_CONFIG = RobotConfig(
    name="go2",
    mjcf_file="go2.xml",
    scene_file="scene.xml",
    assets_dir="assets",
    num_joints=12,
    joint_names=[
        "FR_hip_joint", "FR_thigh_joint", "FR_calf_joint",
        "FL_hip_joint", "FL_thigh_joint", "FL_calf_joint",
        "RR_hip_joint", "RR_thigh_joint", "RR_calf_joint",
        "RL_hip_joint", "RL_thigh_joint", "RL_calf_joint",
    ],
    motor_names=[
        "FR_hip", "FR_thigh", "FR_calf",
        "FL_hip", "FL_thigh", "FL_calf",
        "RR_hip", "RR_thigh", "RR_calf",
        "RL_hip", "RL_thigh", "RL_calf",
    ],
)

# G1 configuration (23 DOF version)
G1_CONFIG = RobotConfig(
    name="g1",
    mjcf_file="g1_23dof.xml",
    scene_file="scene.xml",
    assets_dir="meshes",
    num_joints=23,
    joint_names=[
        # Left leg
        "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
        "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
        # Right leg
        "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
        "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
        # Waist
        "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
        # Left arm
        "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
        "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
        # Right arm (only 1 arm in 23dof)
        "right_shoulder_pitch_joint",
    ],
    motor_names=[
        "left_hip_pitch", "left_hip_roll", "left_hip_yaw",
        "left_knee", "left_ankle_pitch", "left_ankle_roll",
        "right_hip_pitch", "right_hip_roll", "right_hip_yaw",
        "right_knee", "right_ankle_pitch", "right_ankle_roll",
        "waist_yaw", "waist_roll", "waist_pitch",
        "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw",
        "left_elbow", "left_wrist_roll", "left_wrist_pitch", "left_wrist_yaw",
        "right_shoulder_pitch",
    ],
)

# Robot registry
ROBOTS = {
    "go2": GO2_CONFIG,
    "g1": G1_CONFIG,
}


@dataclass
class SimConfig:
    """Simulation configuration."""
    dt: float = 0.002  # Simulation timestep (500 Hz)
    viewer_dt: float = 0.033  # Visualization update (30 Hz)
    web_port: int = 8080
    vuer_port: int = 8012
    default_robot: str = "go2"


# Default simulation config
SIM_CONFIG = SimConfig()
