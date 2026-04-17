# Unitree Workspace Agent Guide

## Workspace Structure

```
unitree_ws/
├── git/official/          # Primary SDK repositories
│   ├── unitree_sdk2/          # C++ SDK (core)
│   ├── unitree_sdk2_python/  # Python SDK
│   ├── unitree_ros2/          # ROS2 integration
│   ├── unitree_mujoco/       # MuJoCo simulation
│   ├── unitree_rl_gym/       # RL training (Isaac Gym)
│   ├── unitree_ros/          # ROS1 + URDF models
│   └── unitree_model/        # USD models
├── git/community/         # Third-party projects (reference only)
├── projects/             # User projects
│   ├── go2_mujoco_vuer/  # MuJoCo web simulation (Go2/G1)
│   ├── go2_inspection/   # LiDAR mapping + inspection
│   └── go2_remote_map/   # Remote map visualization
└── docs/                 # Offline documentation
```

## Critical Constraints (Don't Skip)

- **Cyclonedds version**: MUST use `releases/0.10.x` branch, not latest
- **Network interface**: All robot examples require explicit interface name (e.g., `enp3s0`)
- **ROS2 build order**: Must `source` ROS2 environment BEFORE `colcon build`
- **Motor safety**: Low-level control requires low gains (kp=10, kd=1) for testing
- **Mode conflict**: Must disable sport mode via App before low-level control

## SDK Commands

### C++ SDK Build & Run
```bash
cd git/official/unitree_sdk2
mkdir build && cd build
cmake .. && make
sudo make install

# Run examples (specify network interface)
./bin/go2_sport_client enp3s0    # High-level motion
./bin/go2_low_level enp3s0      # Low-level motor control
```

### Python SDK Install
```bash
# Only if cyclonedds missing:
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install
export CYCLONEDDS_HOME=~/cyclonedds/install

# Install SDK
cd git/official/unitree_sdk2_python
pip3 install -e .
```

### Python Examples
```bash
cd git/official/unitree_sdk2_python
python3 ./example/helloworld/publisher.py
python3 ./example/high_level/sportmode_test.py enp2s0
python3 ./example/low_level/lowlevel_control.py enp2s0
```

### ROS2 Examples
```bash
source ~/unitree_ros2/setup.sh  # Must source first
cd git/official/unitree_ros2/example
colcon build
./install/unitree_ros2_example/bin/read_motion_state
ros2 topic echo /sportmodestate
```

### RL Training (Isaac Gym)
```bash
cd git/official/unitree_rl_gym
python legged_gym/scripts/train.py --task=go2
python legged_gym/scripts/play.py --task=go2

# Sim2Sim deployment
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml
```

## User Projects

### go2_mujoco_vuer (Web Simulation)
```bash
conda env create -f projects/go2_mujoco_vuer/environment.yml
conda activate mujoco-sim
cd projects/go2_mujoco_vuer
python web/app.py
# Access http://localhost:8080
```

### go2_inspection (Mapping + Inspection)
```bash
conda create -n go2-inspection python=3.10 -y
conda activate go2-inspection
cd projects/go2_inspection
pip install -r requirements.txt
./start.sh  # or: python web/app.py
# Access http://localhost:8000
```

### go2_remote_map
```bash
cd projects/go2_remote_map
pip install -r requirements.txt
./start.sh
```

## Key DDS Topics

| Topic | Description |
|-------|-------------|
| `/sportmodestate` | High-level motion state |
| `/lowstate` | Low-level motor + IMU state |
| `/api/sport/request` | High-level control command |
| `/lowcmd` | Low-level motor command |
| `/wirelesscontroller` | Remote controller state |

## Motion Modes

| Code | Mode |
|------|------|
| 0 | Stand/Idle |
| 1 | Balance Stand |
| 2 | Attitude Control |
| 3 | Walk |
| 5 | Lay Down |
| 6 | Lock Joints |
| 7 | Damping |
| 8 | Recovery Stand |
| 10 | Sit |

## Documentation

- Online: https://support.unitree.com/home/en/developer
- Offline: `docs/Unitree_Go2_SDK_文档全集.md`
- SDK READMEs: `git/official/*/README.md`

## Setup Commands

```bash
# Clone workspace
git clone https://github.com/yuyonghua/unitree-workspace.git unitree_ws
cd unitree_ws

# Quick clone official SDK only (recommended)
./setup.sh --shallow

# Clone with community projects
./setup.sh --shallow --community

# Update existing repos
./setup.sh --update
```

## Dependencies

### C++
```bash
sudo apt-get install -y cmake g++ build-essential \
    libyaml-cpp-dev libeigen3-dev libboost-all-dev \
    libspdlog-dev libfmt-dev
```

### ROS2 (Foxy example)
```bash
sudo apt install ros-foxy-rmw-cyclonedds-cpp \
    ros-foxy-rosidl-generator-dds-idl
```

### Python
- Python >= 3.8
- cyclonedds == 0.10.2
- numpy, opencv-python