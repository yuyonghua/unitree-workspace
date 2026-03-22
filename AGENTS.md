# AGENTS.md - Unitree Go2 Development Workspace

This workspace contains Unitree robot SDKs and tools for Go2/B2/H1/G1 development.

## Workspace Structure

```
unitree_ws/
├── git/
│   ├── official/          # PRIMARY REFERENCE - Official Unitree repositories
│   │   ├── unitree_sdk2/            # C++ SDK (core)
│   │   ├── unitree_sdk2_python/     # Python SDK
│   │   ├── unitree_ros2/            # ROS2 integration
│   │   ├── unitree_rl_gym/          # RL training (Isaac Gym)
│   │   ├── unitree_mujoco/          # Mujoco simulation
│   │   └── ...
│   └── community/         # Community projects (reference only, last resort)
├── docs/                  # Self-generated docs (mostly inaccurate)
│   └── Unitree_Go2_SDK_文档全集.md  # Useful: official docs scraped from website
├── sample/                # Test scripts (reference only, low value)
└── projects/              # User projects
```

**IMPORTANT:** Always reference `git/official/` repositories first. Community repos are for understanding only.

## Build Commands

### C++ SDK (unitree_sdk2)
```bash
cd git/official/unitree_sdk2
mkdir build && cd build
cmake ..
make                    # Build examples
sudo make install       # Install to system
# Or install to custom path:
cmake .. -DCMAKE_INSTALL_PREFIX=/opt/unitree_robotics
sudo make install
```

**Dependencies:**
```bash
apt-get install -y cmake g++ build-essential libyaml-cpp-dev \
    libeigen3-dev libboost-all-dev libspdlog-dev libfmt-dev
```

### Python SDK (unitree_sdk2_python)
```bash
cd git/official/unitree_sdk2_python
pip3 install -e .

# If cyclonedds not found, build it first:
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install
export CYCLONEDDS_HOME=~/cyclonedds/install
pip3 install -e .
```

**Dependencies:** Python >= 3.8, cyclonedds == 0.10.2, numpy, opencv-python

### ROS2 Package (unitree_ros2)
```bash
cd git/official/unitree_ros2

# Install dependencies (example for ROS2 foxy):
sudo apt install ros-foxy-rmw-cyclonedds-cpp ros-foxy-rosidl-generator-dds-idl

# Build cyclonedds (skip for Humble):
cd cyclonedds_ws
colcon build --packages-select cyclonedds

# Source ROS2 and build:
source /opt/ros/foxy/setup.bash
colcon build

# Setup environment:
source ~/unitree_ros2/setup.sh
```

**Tested:** Ubuntu 20.04 + Foxy, Ubuntu 22.04 + Humble (recommended)

### RL Gym (unitree_rl_gym)
```bash
cd git/official/unitree_rl_gym

# Training:
python legged_gym/scripts/train.py --task=go2

# Play (visualize):
python legged_gym/scripts/play.py --task=go2

# Sim2Sim (Mujoco):
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml

# Sim2Real (physical robot):
python deploy/deploy_real/deploy_real.py enp3s0 g1.yaml
```

## Running Examples

### C++ Examples
```bash
cd git/official/unitree_sdk2/build
./bin/go2_sport_client enp3s0    # High-level control
./bin/go2_low_level enp3s0       # Low-level control
./bin/publisher                  # DDS publish test
./bin/subscriber                 # DDS subscribe test
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
source ~/unitree_ros2/setup.sh
cd git/official/unitree_ros2/example
colcon build
./install/unitree_ros2_example/bin/read_motion_state
ros2 topic list
ros2 topic echo /sportmodestate
```

## Robot Connection

1. Connect computer to robot via Ethernet
2. Configure network interface (e.g., `enp3s0`):
   - IP: `192.168.123.99`
   - Netmask: `255.255.255.0`
3. Replace `enp3s0` in commands with your interface name

## Code Style

### C++ (Google Style)
Configured via `.clang-format` and `.clang-tidy` in unitree_ros2:

- **Style:** Based on Google C++ Style
- **Classes:** `CamelCase`
- **Functions:** `lower_case`
- **Private members:** `lower_case_` (trailing underscore)
- **Enums:** `CamelCase` type, `UPPER_CASE` constants
- **Standard:** C++17

```cpp
// Example from official SDK
#include <unitree/robot/channel/channel_publisher.hpp>

using namespace unitree::robot;

class MyController {
public:
    void InitChannel();
private:
    ChannelPublisher<Msg> publisher_;
};
```

### Python
- Follow PEP 8
- Use type hints where practical
- snake_case for functions/variables

```python
# Example from official SDK
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize

def main():
    ChannelFactoryInitialize()
    pub = ChannelPublisher("topic", UserData)
    pub.Init()
```

## Testing

No formal test suite exists in official repos. Verify by:
1. Building without errors
2. Running examples against robot/simulator
3. Checking DDS communication (publisher/subscriber pair)

## Key Interfaces

### DDS Topics (Go2)
- `/sportmodestate` - High-level motion state
- `/lowstate` - Low-level motor/IMU state
- `/api/sport/request` - High-level control commands
- `/lowcmd` - Low-level motor commands
- `/wirelesscontroller` - Remote controller state

### Sport Modes
```
0: idle/stand    1: balanceStand  2: pose
3: locomotion    5: lieDown       6: jointLock
7: damping       8: recoveryStand 10: sit
```

## Documentation Reference

Primary: `git/official/` repository READMEs and code
Secondary: `docs/Unitree_Go2_SDK_文档全集.md` (official docs, Chinese)
Official: https://support.unitree.com/home/en/developer

## Common Pitfalls

1. **Cyclonedds version:** Must use 0.10.x for compatibility
2. **Network interface:** Always specify correct interface name
3. **ROS2 sourcing:** Source environment before building/running
4. **Safety:** Use low kp/kd values (kp=10, kd=1) when testing motor control
5. **Sport mode conflict:** Disable high-level mode via App before low-level control
