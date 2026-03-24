#!/bin/bash
# Clone Go2 robot repositories from Unitree official GitHub
# Usage: ./clone_go2_repos.sh

set -e

echo "=========================================="
echo "  Unitree Go2 Robot Repositories"
echo "=========================================="

# ============================================
# Core SDK (核心SDK)
# ============================================
echo ""
echo "[1/7] Cloning Core SDK..."
git clone https://github.com/unitreerobotics/unitree_sdk2.git
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git

# ============================================
# ROS Integration (ROS集成)
# ============================================
echo ""
echo "[2/7] Cloning ROS packages..."
git clone https://github.com/unitreerobotics/unitree_ros2.git
git clone https://github.com/unitreerobotics/unitree_ros.git

# ============================================
# Simulation (仿真)
# ============================================
echo ""
echo "[3/7] Cloning Simulation packages..."
git clone https://github.com/unitreerobotics/unitree_mujoco.git
git clone https://github.com/unitreerobotics/unitree_rl_gym.git

# ============================================
# Perception (感知) - SLAM with Lidar L1
# ============================================
echo ""
echo "[4/7] Cloning Perception packages..."
git clone https://github.com/unitreerobotics/point_lio_unilidar.git

# ============================================
# 3D Models (3D模型) - USD for Isaac Sim
# ============================================
echo ""
echo "[5/7] Cloning 3D Models..."
git clone https://github.com/unitreerobotics/unitree_model.git

# ============================================
# Advanced RL (高级强化学习) - Optional
# ============================================
echo ""
echo "[6/7] Cloning Advanced RL packages..."
# git clone https://github.com/unitreerobotics/unitree_rl_lab.git
# git clone https://github.com/unitreerobotics/unitree_rl_mjlab.git

# ============================================
# AGI (通用人工智能) - Optional/Experimental
# ============================================
echo ""
echo "[7/7] Cloning AGI packages..."
# git clone https://github.com/unitreerobotics/unifolm-world-model-action.git

echo ""
echo "=========================================="
echo "  Not for Go2 (commented out)"
echo "=========================================="
echo ""
echo "# --- Humanoid Robot (人形机器人) ---"
# git clone https://github.com/unitreerobotics/unifolm-vla.git
# git clone https://github.com/unitreerobotics/xr_teleoperate.git
# git clone https://github.com/unitreerobotics/unitree_lerobot.git
# git clone https://github.com/unitreerobotics/unitree_sim_isaaclab.git
#
echo "# --- Legacy SDK (旧版SDK, for A1/Go1/B1/AlienGo) ---"
# git clone https://github.com/unitreerobotics/unitree_legged_sdk.git
#
echo "# --- Other ---"
# git clone https://github.com/unitreerobotics/unitree_guide.git
# git clone https://github.com/unitreerobotics/teleimager.git

echo ""
echo "=========================================="
echo "  Clone completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Build C++ SDK:    cd unitree_sdk2 && cmake -Bbuild && cmake --build build -j\$(nproc)"
echo "  2. Build Python SDK: cd unitree_sdk2_python && pip3 install -e ."
echo "  3. Build ROS2:       cd unitree_ros2 && colcon build"
echo ""
