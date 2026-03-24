# AGENTS.md - Unitree 机器人开发工作空间

Unitree 机器人 SDK，适用于 Go2/B2/H1/G1/G2/R1/A2 开发。

## 工作空间结构

```
unitree_ws/
├── git/
│   ├── official/          # 主要参考 - Unitree 官方仓库
│   │   ├── unitree_sdk2/            # C++ SDK（核心）
│   │   ├── unitree_sdk2_python/     # Python SDK
│   │   ├── unitree_ros2/            # ROS2 通信包
│   │   ├── unitree_ros/             # URDF/3D 模型
│   │   ├── unitree_rl_gym/          # 强化学习训练（Isaac Gym）
│   │   ├── unitree_mujoco/          # Mujoco 仿真
│   │   └── point_lio_unilidar/      # 4D Lidar L1 SLAM
│   └── community/         # 社区项目（仅供参考，最后手段）
├── docs/                  # 自生成文档（大多不准确）
├── sample/                # 测试脚本（参考价值有限）
└── projects/              # 用户项目
```

**重要：** 始终优先参考 `git/official/` 仓库。社区仓库仅供了解。

## 构建命令

### C++ SDK (unitree_sdk2)
```bash
# 依赖安装
sudo apt-get install -y cmake g++ build-essential libyaml-cpp-dev \
    libeigen3-dev libboost-all-dev libspdlog-dev libfmt-dev

# 构建
cd git/official/unitree_sdk2
cmake -Bbuild
cmake --build build -j$(nproc)
sudo cmake --install build
```

### Python SDK (unitree_sdk2_python)
```bash
cd git/official/unitree_sdk2_python
pip3 install -e .

# 如果提示 cyclonedds 未找到，需先编译：
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install && cmake --build . --target install
export CYCLONEDDS_HOME=~/cyclonedds/install
pip3 install -e .
```

**依赖：** Python >= 3.8, cyclonedds == 0.10.2, numpy, opencv-python

### ROS2 包 (unitree_ros2)
```bash
cd git/official/unitree_ros2
sudo apt install ros-humble-rmw-cyclonedds-cpp ros-humble-rosidl-generator-dds-idl

# 先编译 cyclonedds
cd cyclonedds_ws
git clone https://github.com/ros2/rmw_cyclonedds -b humble
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd .. && colcon build --packages-select cyclonedds

# 编译包
source /opt/ros/humble/setup.sh
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
colcon build --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

**测试环境：** Ubuntu 22.04 + Humble（推荐）, Ubuntu 20.04 + Foxy

### 强化学习 Gym (unitree_rl_gym)
```bash
cd git/official/unitree_rl_gym
python legged_gym/scripts/train.py --task=go2      # 训练
python legged_gym/scripts/play.py --task=go2       # 可视化
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml   # Sim2Sim
python deploy/deploy_real/deploy_real.py enp3s0 g1.yaml # Sim2Real
```

## 运行示例

```bash
# C++ 示例
cd git/official/unitree_sdk2/build
./bin/go2_sport_client enp3s0    # 高层运动控制
./bin/go2_low_level enp3s0       # 底层电机控制

# Python 示例
cd git/official/unitree_sdk2_python
python3 ./example/high_level/sportmode_test.py enp3s0

# ROS2 示例
source ~/unitree_ros2/setup.sh
ros2 topic echo /sportmodestate
```

## 代码风格

### C++ (Google 风格)
通过 unitree_ros2 中的 `.clang-format` 配置：
```yaml
Language: Cpp
BasedOnStyle: Google
```

**约定：**
- **类名：** `CamelCase`
- **函数/变量：** `lower_case`
- **私有成员：** `lower_case_`（尾部下划线）
- **枚举：** `CamelCase` 类型，`UPPER_CASE` 常量
- **标准：** C++17

### Python (PEP 8)
- 函数/变量使用 snake_case
- 尽可能使用类型提示
- 无正式 linter 配置（pyproject.toml 最简）

## 测试

官方仓库无正式测试套件。验证方法：
1. 构建无错误
2. 对机器人/仿真器运行示例
3. 检查 DDS 通信（发布/订阅对）

**CI 工作流：** unitree_sdk2 和 unitree_ros2 的 `.github/workflows/` 中有 GitHub Actions

## 关键接口

### DDS 话题 (Go2/B2/H1/G1)
| 话题 | 描述 |
|-------|-------------|
| `/sportmodestate` | 高层运动状态 |
| `/lowstate` | 底层电机/IMU 状态 |
| `/api/sport/request` | 高层控制命令 |
| `/lowcmd` | 底层电机命令 |
| `/wirelesscontroller` | 遥控器状态 |

### 运动模式
| 代码 | 模式 |
|------|------|
| 0 | 待机/站立 |
| 1 | 平衡站立 |
| 2 | 姿态控制 |
| 3 | 运动行走 |
| 5 | 趴下 |
| 6 | 关节锁定 |
| 7 | 阻尼 |
| 8 | 恢复站立 |
| 10 | 坐下 |

## 机器人连接

1. 通过以太网连接电脑和机器人
2. 配置网络接口（如 `enp3s0`）：
   - IP：`192.168.123.99`，子网掩码：`255.255.255.0`
3. 在命令中将 `enp3s0` 替换为你的接口名称

## 文档参考

- **主要参考：** `git/official/` 各仓库 README 和代码
- **次要参考：** `docs/Unitree_Go2_SDK_文档全集.md`（官方文档，中文）
- **官方文档：** https://support.unitree.com/home/en/developer

## 常见问题

1. **Cyclonedds 版本：** 必须使用 0.10.x 版本
2. **网络接口：** 始终指定正确的接口名称
3. **ROS2 环境：** 构建前需先 source ROS2 环境
4. **安全测试：** 测试电机控制时使用较低的 kp/kd 值（kp=10, kd=1）
5. **模式冲突：** 使用底层控制前需通过 App 关闭高层运动模式
