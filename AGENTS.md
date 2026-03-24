# AGENTS.md - Unitree Robot Development Workspace

Unitree robot SDKs for Go2/B2/H1/G1/G2/R1/A2 development.

## Workspace Structure

```
unitree_ws/
├── git/
│   ├── official/          # PRIMARY REFERENCE - Official Unitree repositories
│   │   ├── unitree_sdk2/            # C++ SDK (core)
│   │   ├── unitree_sdk2_python/     # Python SDK
│   │   ├── unitree_ros2/            # ROS2 communication package
│   │   ├── unitree_ros/             # URDF/3D models for all robots
│   │   ├── unitree_rl_gym/          # RL training (Isaac Gym)
│   │   ├── unitree_mujoco/          # Mujoco simulation
│   │   └── point_lio_unilidar/      # SLAM with 4D Lidar L1
│   └── community/         # Community projects (reference only, last resort)
├── docs/                  # Self-generated docs (mostly inaccurate)
├── sample/                # Test scripts (reference only, low value)
└── projects/              # User projects
```

**CRITICAL:** Always reference `git/official/` repositories first. Community repos are for understanding only.

## Build Commands

### C++ SDK (unitree_sdk2)
```bash
# Dependencies
sudo apt-get install -y cmake g++ build-essential libyaml-cpp-dev \
    libeigen3-dev libboost-all-dev libspdlog-dev libfmt-dev

# Build
cd git/official/unitree_sdk2
cmake -Bbuild
cmake --build build -j$(nproc)
sudo cmake --install build
```

### Python SDK (unitree_sdk2_python)
```bash
cd git/official/unitree_sdk2_python
pip3 install -e .

# If cyclonedds not found, build it first:
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install && cmake --build . --target install
export CYCLONEDDS_HOME=~/cyclonedds/install
pip3 install -e .
```

**Dependencies:** Python >= 3.8, cyclonedds == 0.10.2, numpy, opencv-python

### ROS2 Package (unitree_ros2)
```bash
cd git/official/unitree_ros2
sudo apt install ros-humble-rmw-cyclonedds-cpp ros-humble-rosidl-generator-dds-idl

# Build cyclonedds first
cd cyclonedds_ws
git clone https://github.com/ros2/rmw_cyclonedds -b humble
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd .. && colcon build --packages-select cyclonedds

# Build packages
source /opt/ros/humble/setup.sh
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
colcon build --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

**Tested:** Ubuntu 22.04 + Humble (recommended), Ubuntu 20.04 + Foxy

### RL Gym (unitree_rl_gym)
```bash
cd git/official/unitree_rl_gym
python legged_gym/scripts/train.py --task=go2      # Training
python legged_gym/scripts/play.py --task=go2       # Visualize
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml   # Sim2Sim
python deploy/deploy_real/deploy_real.py enp3s0 g1.yaml # Sim2Real
```

## Running Examples

```bash
# C++ Examples
cd git/official/unitree_sdk2/build
./bin/go2_sport_client enp3s0    # High-level control
./bin/go2_low_level enp3s0       # Low-level control

# Python Examples
cd git/official/unitree_sdk2_python
python3 ./example/high_level/sportmode_test.py enp3s0

# ROS2 Examples
source ~/unitree_ros2/setup.sh
ros2 topic echo /sportmodestate
```

## Code Style

### C++ (Google Style)
Configured via `.clang-format` in unitree_ros2:
```yaml
Language: Cpp
BasedOnStyle: Google
```

**Conventions:**
- **Classes:** `CamelCase`
- **Functions/variables:** `lower_case`
- **Private members:** `lower_case_` (trailing underscore)
- **Enums:** `CamelCase` type, `UPPER_CASE` constants
- **Standard:** C++17

### Python (PEP 8)
- snake_case for functions/variables
- Use type hints where practical
- No formal linter configured (pyproject.toml minimal)

## Testing

No formal test suite exists in official repos. Verify by:
1. Building without errors
2. Running examples against robot/simulator
3. Checking DDS communication (publisher/subscriber pair)

**CI Workflows:** GitHub Actions in `.github/workflows/` for unitree_sdk2 and unitree_ros2

## Key Interfaces

### DDS Topics (Go2/B2/H1/G1)
| Topic | Description |
|-------|-------------|
| `/sportmodestate` | High-level motion state |
| `/lowstate` | Low-level motor/IMU state |
| `/api/sport/request` | High-level control commands |
| `/lowcmd` | Low-level motor commands |
| `/wirelesscontroller` | Remote controller state |

### Sport Modes
| Code | Mode |
|------|------|
| 0 | idle/stand |
| 1 | balanceStand |
| 2 | pose |
| 3 | locomotion |
| 5 | lieDown |
| 6 | jointLock |
| 7 | damping |
| 8 | recoveryStand |
| 10 | sit |

## Robot Connection

1. Connect computer to robot via Ethernet
2. Configure network interface (e.g., `enp3s0`):
   - IP: `192.168.123.99`, Netmask: `255.255.255.0`
3. Replace `enp3s0` in commands with your interface name

## Documentation Reference

- **Primary:** `git/official/` repository READMEs and code
- **Secondary:** `docs/Unitree_Go2_SDK_文档全集.md` (official docs, Chinese)
- **Official:** https://support.unitree.com/home/en/developer

## Common Pitfalls

1. **Cyclonedds version:** Must use 0.10.x for compatibility
2. **Network interface:** Always specify correct interface name
3. **ROS2 sourcing:** Source environment before building/running
4. **Safety:** Use low kp/kd values (kp=10, kd=1) when testing motor control
5. **Sport mode conflict:** Disable high-level mode via App before low-level control
