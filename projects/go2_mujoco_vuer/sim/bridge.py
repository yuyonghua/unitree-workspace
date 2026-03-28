"""DDS Bridge for Unitree SDK2 communication.

This module bridges MuJoCo simulation with Unitree SDK2:
- Publishes simulated robot state via DDS
- Receives control commands via DDS
- Supports both Go2 (unitree_go) and G1 (unitree_hg) message types
"""

import time
import threading
import numpy as np
from typing import Optional
from dataclasses import dataclass

try:
    from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowState_
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_, LowState_
    from unitree_sdk2py.utils.crc import CRC
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("Warning: unitree_sdk2py not installed. DDS bridge disabled.")

from config import RobotConfig, SimConfig


class DDSBridge:
    """Bridge between MuJoCo simulation and Unitree DDS."""

    def __init__(self, robot_config: RobotConfig, sim_config: SimConfig):
        self.robot_config = robot_config
        self.sim_config = sim_config

        if not SDK_AVAILABLE:
            raise RuntimeError("unitree_sdk2py not available. Install it first.")

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # DDS publishers/subscribers
        self.lowstate_pub: Optional[ChannelPublisher] = None
        self.lowcmd_sub: Optional[ChannelSubscriber] = None

        # Latest commands from SDK
        self.latest_cmd = None
        self.cmd_lock = threading.Lock()

        # CRC calculator
        self.crc = CRC()

    def start(self):
        """Start DDS bridge."""
        if self.running:
            return

        # Initialize DDS factory
        ChannelFactoryInitialize(self.sim_config.domain_id, self.robot_config.interface)

        # Create publisher for robot state
        self.lowstate_pub = ChannelPublisher("rt/lowstate", LowState_)
        self.lowstate_pub.Init()

        # Create subscriber for control commands
        self.lowcmd_sub = ChannelSubscriber("rt/lowcmd", LowCmd_)
        self.lowcmd_sub.Init(self._lowcmd_handler)

        self.running = True
        print(f"DDS bridge started: domain={self.sim_config.domain_id}, interface={self.robot_config.interface}")

    def stop(self):
        """Stop DDS bridge."""
        self.running = False
        if self.lowstate_pub:
            self.lowstate_pub.Close()
        if self.lowcmd_sub:
            self.lowcmd_sub.Close()
        print("DDS bridge stopped")

    def _lowcmd_handler(self, msg):
        """Handle incoming control commands."""
        with self.cmd_lock:
            self.latest_cmd = msg

    def get_control(self) -> Optional[np.ndarray]:
        """Get latest control command from SDK."""
        with self.cmd_lock:
            if self.latest_cmd is None:
                return None

            # Extract motor commands
            cmd = self.latest_cmd
            ctrl = np.zeros(self.robot_config.num_joints)

            for i in range(min(len(ctrl), 12)):  # Go2 has 12 motors
                ctrl[i] = cmd.motor_cmd[i].q  # Position command

            return ctrl

    def publish_state(self, joint_pos: np.ndarray, joint_vel: np.ndarray,
                      joint_tau: np.ndarray, imu_quat: np.ndarray,
                      imu_gyro: np.ndarray, imu_acc: np.ndarray):
        """Publish simulated robot state via DDS."""
        if not self.lowstate_pub:
            return

        # Create LowState message
        state = unitree_go_msg_dds__LowState_()

        # IMU state
        state.imu_state.quaternion = imu_quat.tolist()
        state.imu_state.gyroscope = imu_gyro.tolist()
        state.imu_state.accelerometer = imu_acc.tolist()

        # Motor states
        for i in range(min(12, len(joint_pos))):
            state.motor_state[i].q = float(joint_pos[i])
            state.motor_state[i].dq = float(joint_vel[i])
            state.motor_state[i].tau_est = float(joint_tau[i])
            state.motor_state[i].mode = 0x01  # PMSM mode

        # CRC
        state.crc = self.crc.Crc(state)

        # Publish
        self.lowstate_pub.Write(state)


def create_bridge(robot_config: RobotConfig, sim_config: SimConfig) -> Optional[DDSBridge]:
    """Create DDS bridge if SDK is available."""
    if not SDK_AVAILABLE:
        print("DDS bridge not available (SDK not installed)")
        return None

    try:
        return DDSBridge(robot_config, sim_config)
    except Exception as e:
        print(f"Failed to create DDS bridge: {e}")
        return None
