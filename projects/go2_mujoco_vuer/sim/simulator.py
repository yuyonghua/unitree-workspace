"""MuJoCo simulation manager for Go2/G1 robots.

This module manages the MuJoCo simulation lifecycle:
- Load MJCF models
- Step physics simulation
- Read robot state (qpos, qvel, sensors)
- Provide state to web visualization
"""

import time
import threading
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable

import mujoco

from config import RobotConfig, SimConfig, MUJOCO_ROBOTS_DIR


@dataclass
class RobotState:
    """Current robot state from simulation."""
    timestamp: float = 0.0
    qpos: np.ndarray = field(default_factory=lambda: np.zeros(7))  # base position + quaternion
    qvel: np.ndarray = field(default_factory=lambda: np.zeros(6))  # base velocity
    joint_pos: np.ndarray = field(default_factory=lambda: np.zeros(12))  # joint positions
    joint_vel: np.ndarray = field(default_factory=lambda: np.zeros(12))  # joint velocities
    joint_tau: np.ndarray = field(default_factory=lambda: np.zeros(12))  # joint torques
    imu_quat: np.ndarray = field(default_factory=lambda: np.zeros(4))  # IMU quaternion
    imu_gyro: np.ndarray = field(default_factory=lambda: np.zeros(3))  # IMU gyroscope
    imu_acc: np.ndarray = field(default_factory=lambda: np.zeros(3))  # IMU accelerometer
    foot_pos: np.ndarray = field(default_factory=lambda: np.zeros(12))  # foot positions (4 feet × 3D)


class MuJoCoSimulator:
    """MuJoCo simulation manager."""

    def __init__(self, robot_config: RobotConfig, sim_config: SimConfig):
        self.robot_config = robot_config
        self.sim_config = sim_config

        # MuJoCo objects
        self.model: Optional[mujoco.MjModel] = None
        self.data: Optional[mujoco.MjData] = None

        # Simulation state
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Current state
        self.state = RobotState()

        # State callback for external consumers (e.g., web server)
        self.state_callback: Optional[Callable[[RobotState], None]] = None

        # Control commands (shared with control thread)
        self.ctrl = np.zeros(12)

    def load_model(self, robot_name: Optional[str] = None) -> bool:
        """Load MuJoCo model for specified robot."""
        if robot_name and robot_name != self.robot_config.name:
            from config import ROBOTS
            if robot_name not in ROBOTS:
                raise ValueError(f"Unknown robot: {robot_name}")
            self.robot_config = ROBOTS[robot_name]

        # Build model path
        model_dir = MUJOCO_ROBOTS_DIR / self.robot_config.name
        scene_path = model_dir / self.robot_config.scene_file

        if not scene_path.exists():
            raise FileNotFoundError(f"Scene file not found: {scene_path}")

        print(f"Loading MuJoCo model: {scene_path}")

        # Load model
        self.model = mujoco.MjModel.from_xml_path(str(scene_path))
        self.data = mujoco.MjData(self.model)

        # Initialize control
        self.ctrl = np.zeros(self.model.nu)

        # Reset to home position
        mujoco.mj_resetDataKeyframe(self.model, self.data, 0)

        print(f"Model loaded: {self.model.nbody} bodies, {self.model.njnt} joints, {self.model.nu} actuators")
        return True

    def start(self):
        """Start simulation thread."""
        if self.running:
            print("Simulation already running")
            return

        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        self.running = True
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()
        print(f"Simulation started: dt={self.sim_config.dt}s, robot={self.robot_config.name}")

    def stop(self):
        """Stop simulation thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        print("Simulation stopped")

    def _simulation_loop(self):
        """Main simulation loop."""
        while self.running:
            step_start = time.perf_counter()

            with self.lock:
                # Apply control
                self.data.ctrl[:] = self.ctrl

                # Step physics
                mujoco.mj_step(self.model, self.data)

                # Update state
                self._update_state()

            # Call state callback if registered
            if self.state_callback:
                self.state_callback(self.state)

            # Maintain timing
            elapsed = time.perf_counter() - step_start
            sleep_time = self.sim_config.dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _update_state(self):
        """Update robot state from simulation data."""
        self.state.timestamp = self.data.time

        # Base position and orientation (first 7 qpos values)
        self.state.qpos = self.data.qpos[:7].copy()

        # Base velocity (first 6 qvel values)
        self.state.qvel = self.data.qvel[:6].copy()

        # Joint positions (skip first 7 qpos: 3 pos + 4 quat)
        n_joints = min(self.robot_config.num_joints, len(self.data.qpos) - 7)
        self.state.joint_pos[:n_joints] = self.data.qpos[7:7 + n_joints]

        # Joint velocities
        self.state.joint_vel[:n_joints] = self.data.qvel[6:6 + n_joints]

        # Joint torques
        self.state.joint_tau[:n_joints] = self.data.qfrc_actuator[:n_joints]

        # Read sensors if available
        self._read_sensors()

    def _read_sensors(self):
        """Read sensor data from MuJoCo."""
        try:
            # IMU quaternion
            imu_quat = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "imu")
            if imu_quat >= 0:
                self.state.imu_quat = self.data.site_xquat[imu_quat].copy()
        except Exception:
            pass

        # Foot positions (compute from body positions)
        foot_names = ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]
        for i, name in enumerate(foot_names):
            try:
                body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, name)
                if body_id >= 0:
                    self.state.foot_pos[i * 3:(i + 1) * 3] = self.data.xpos[body_id]
            except Exception:
                pass

    def set_control(self, ctrl: np.ndarray):
        """Set motor control commands."""
        with self.lock:
            n_ctrl = min(len(ctrl), len(self.ctrl))
            self.ctrl[:n_ctrl] = ctrl[:n_ctrl]

    def get_state(self) -> RobotState:
        """Get current robot state (thread-safe)."""
        with self.lock:
            return self.state

    def reset(self):
        """Reset simulation to initial state."""
        with self.lock:
            if self.model and self.data:
                mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
                self.ctrl[:] = 0
                self._update_state()
            print("Simulation reset")

    def get_model_info(self) -> dict:
        """Get model information for visualization."""
        if self.model is None:
            return {}

        return {
            "name": self.robot_config.name,
            "nbody": self.model.nbody,
            "njnt": self.model.njnt,
            "nu": self.model.nu,
            "nq": self.model.nq,
            "joint_names": self.robot_config.joint_names,
            "motor_names": self.robot_config.motor_names,
        }


# Singleton instance
_simulator: Optional[MuJoCoSimulator] = None


def get_simulator(robot_config: RobotConfig = None, sim_config: SimConfig = None) -> MuJoCoSimulator:
    """Get or create simulator singleton."""
    global _simulator
    if _simulator is None:
        from config import GO2_CONFIG, SIM_CONFIG
        _simulator = MuJoCoSimulator(
            robot_config or GO2_CONFIG,
            sim_config or SIM_CONFIG,
        )
    return _simulator
