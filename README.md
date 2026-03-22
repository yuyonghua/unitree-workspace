# Unitree Go2 Development Workspace

Unitree四足机器人开发工作空间，包含Go2/B2/H1/G1的官方SDK、ROS2集成、强化学习训练环境和Mujoco仿真。

## 快速开始

### 1. 克隆工作空间

```bash
git clone --recursive https://github.com/yuyonghua/unitree-workspace.git unitree_ws
cd unitree_ws
```

### 2. 网络配置

通过以太网连接机器人，配置网络接口：

```bash
# 查看网络接口名称
ip addr

# 配置静态IP（以enp3s0为例）
sudo ip addr add 192.168.123.99/24 dev enp3s0
```

### 3. 安装C++ SDK

```bash
cd git/official/unitree_sdk2
mkdir build && cd build
cmake ..
make
sudo make install
```

### 4. 安装Python SDK

```bash
cd git/official/unitree_sdk2_python
pip3 install -e .

# 如果提示cyclonedds未找到，需要先编译：
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install
export CYCLONEDDS_HOME=~/cyclonedds/install
pip3 install -e .
```

## 工作空间结构

```
unitree_ws/
├── git/
│   ├── official/          # 官方SDK仓库（主要参考）
│   │   ├── unitree_sdk2/            # C++ SDK（核心）
│   │   ├── unitree_sdk2_python/     # Python SDK
│   │   ├── unitree_ros2/            # ROS2集成
│   │   ├── unitree_rl_gym/          # 强化学习训练（Isaac Gym）
│   │   ├── unitree_mujoco/          # Mujoco仿真
│   │   └── ...
│   └── community/         # 社区项目（仅作了解参考）
├── docs/                  # 文档
│   └── Unitree_Go2_SDK_文档全集.md  # 官方文档离线版
├── sample/                # 测试脚本（参考价值有限）
└── projects/              # 用户项目
```

## 运行示例

### C++ 示例

```bash
cd git/official/unitree_sdk2/build
./bin/go2_sport_client enp3s0    # 高层运动控制
./bin/go2_low_level enp3s0       # 底层电机控制
./bin/publisher                  # DDS发布测试
./bin/subscriber                 # DDS订阅测试
```

### Python 示例

```bash
cd git/official/unitree_sdk2_python
python3 ./example/helloworld/publisher.py
python3 ./example/high_level/sportmode_test.py enp2s0
python3 ./example/low_level/lowlevel_control.py enp2s0
```

### ROS2 示例

```bash
source ~/unitree_ros2/setup.sh
cd git/official/unitree_ros2/example
colcon build
./install/unitree_ros2_example/bin/read_motion_state
ros2 topic list
ros2 topic echo /sportmodestate
```

### 强化学习训练

```bash
cd git/official/unitree_rl_gym

# 训练
python legged_gym/scripts/train.py --task=go2

# 可视化
python legged_gym/scripts/play.py --task=go2

# Sim2Sim (Mujoco)
python deploy/deploy_mujoco/deploy_mujoco.py g1.yaml

# Sim2Real (真实机器人)
python deploy/deploy_real/deploy_real.py enp3s0 g1.yaml
```

## 依赖安装

### C++ 依赖

```bash
sudo apt-get install -y cmake g++ build-essential \
    libyaml-cpp-dev libeigen3-dev libboost-all-dev \
    libspdlog-dev libfmt-dev
```

### Python 依赖

- Python >= 3.8
- cyclonedds == 0.10.2
- numpy
- opencv-python

### ROS2 依赖（以Foxy为例）

```bash
sudo apt install ros-foxy-rmw-cyclonedds-cpp \
    ros-foxy-rosidl-generator-dds-idl
```

## 关键DDS话题

| 话题 | 描述 |
|------|------|
| `/sportmodestate` | 高层运动状态 |
| `/lowstate` | 底层电机/IMU状态 |
| `/api/sport/request` | 高层控制命令 |
| `/lowcmd` | 底层电机命令 |
| `/wirelesscontroller` | 遥控器状态 |

## 运动模式

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

## 注意事项

1. **Cyclonedds版本**：必须使用0.10.x版本
2. **网络接口**：运行示例时需指定正确的网络接口名称
3. **ROS2环境**：构建前需先source ROS2环境
4. **安全测试**：测试电机控制时使用较低的kp/kd值（kp=10, kd=1）
5. **模式冲突**：使用底层控制前需通过App关闭高层运动模式

## 文档参考

- **官方文档**：`git/official/` 各仓库README
- **离线文档**：`docs/Unitree_Go2_SDK_文档全集.md`（中文，从官网爬取）
- **在线文档**：https://support.unitree.com/home/en/developer

## 许可证

各SDK和工具遵循其原始仓库的许可证。详见各目录下的LICENSE文件。
