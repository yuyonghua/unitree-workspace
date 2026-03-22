# AGENTS.md - Unitree Robot Workspace Guide

This workspace is a **Unitree Go2 robot development environment** containing official SDKs, community libraries, and user projects spanning Python (WebRTC, ROS2, simulation) and C++ (SDK2, ROS2).

## Workspace Structure

```
unitree_ws/
├── docs/              # API documentation (Chinese)
├── git/
│   ├── official/      # Unitree repos: sdk2, ros2, mujoco, rl_gym
│   └── community/     # Community: webrtc_connect, go2_ros2_sdk
├── projects/          # User projects (go2_remote_map)
├── sample/            # Quick-start scripts
```

## Build & Run Commands

### Python Projects (projects/, sample/)

```bash
# Install dependencies
pip install -r projects/go2_remote_map/requirements.txt
cd git/community/unitree_webrtc_connect && pip install -e .

# Run project
cd projects/go2_remote_map && ./start.sh
./start.sh --mode localsta --ip 10.114.97.227
./start.sh --mode remote --serial <SERIAL> --user <EMAIL> --pass <PWD>

# System deps for audio
sudo apt install -y python3-pip portaudio19-dev
```

### C++ Projects (git/official/)

```bash
# CMake build pattern
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### ROS2 Projects

```bash
cd git/official/unitree_ros2/example
colcon build --packages-select <package_name>
source install/setup.bash
ros2 launch go2_robot_sdk robot.launch.py
```

### Testing

```bash
pytest git/official/unitree_mujoco/simulate_python/test/
./build/test_unitree_sdk2  # C++ tests are compiled executables
```

## Python Code Style

### Imports (enforced pattern)
```python
# 1. stdlib
import asyncio
from typing import Optional, Dict, Any

# 2. third-party (blank line separator)
import numpy as np
from fastapi import FastAPI

# 3. local/project (blank line separator)
from config import WEB_CONFIG
from robot import RobotDriver
```

### Naming Conventions
- **Classes**: `PascalCase` — `RobotDriver`, `LidarCollector`
- **Functions/methods**: `snake_case` — `connect_remote()`, `switch_to_normal()`
- **Constants**: `UPPER_CASE` — `WEB_CONFIG`, `SPEED_LIMITS`
- **Private methods**: `_leading_underscore` — `_check()`, `_simple_action()`

### Type Hints
Used on public APIs; internal helpers may omit:
```python
async def connect_remote(self, serial: str, username: str, password: str) -> Dict[str, Any]:
def _extract_points(self, message: dict) -> Optional[np.ndarray]:
```

### Docstrings
Triple-quoted, brief descriptions (often Chinese), no enforced format:
```python
def move(self, x: float, y: float, yaw: float) -> Dict[str, Any]:
    """发送持续移动指令 (Move api_id=1008)"""
```

### Error Handling
Return structured dicts. Log with `logger.error(f"...: {e}")`:
```python
try:
    await self.conn.connect()
    return {"success": True, "message": "connected"}
except Exception as e:
    logger.error(f"连接失败: {e}")
    return {"success": False, "message": str(e)}
```

### Logging
```python
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)
```

## C++ Code Style (unitree_sdk2, unitree_ros2)

### Includes
Order: system headers → third-party → project headers. `<>` for system/third-party, `""` for local:
```cpp
#include <cstdint>
#include <rclcpp/rclcpp.hpp>
#include "time_tools.hpp"
```

### Header Guards
Both `#pragma once` and `#ifndef` used. Prefer `#pragma once` for new code.

### Naming
- **Classes/structs**: `PascalCase` — `BaseClient`, `BoxPointType`
- **Methods**: `CamelCase` — `InitRosComm()`, `WaitForConnection()`
- **Member variables**: `trailing_underscore_` — `node_`, `topic_name_request_`
- **Macros/constants**: `ALL_CAPS` — `UT_OK`, `UT_ERR_COMMON`

### Error Handling
Use SDK error codes (UT_* macros). Catch exceptions only at boundaries:
```cpp
try {
    js = nlohmann::json::parse(received_response_->data.data());
    return UT_ROBOT_SUCCESS;
} catch (const nlohmann::detail::exception& e) {
    return UT_ROBOT_TASK_UNKNOWN_ERROR;
}
```

## Key Libraries & SDKs

| Library | Location | Purpose |
|---------|----------|---------|
| `unitree_webrtc_connect` | `git/community/` | Python WebRTC control for Go2/G1 |
| `unitree_sdk2` | `git/official/` | C++ DDS-based SDK |
| `unitree_ros2` | `git/official/` | ROS2 integration packages |
| `unitree_mujoco` | `git/official/` | MuJoCo simulation environment |

## Common Patterns

### WebRTC Connection (Python)
```python
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="10.114.97.227")
await conn.connect()
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"], {"api_id": SPORT_CMD["StandUp"]}
)
```

### Configuration (Python)
Module-level `UPPER_CASE` dicts in `config.py`:
```python
DEFAULT_REMOTE = {"serial_number": "...", "username": "...", "password": "..."}
SPEED_LIMITS = {"vx": 1.0, "vy": 0.6, "vz": 1.0}
```
