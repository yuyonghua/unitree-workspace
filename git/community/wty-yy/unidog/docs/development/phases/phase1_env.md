# 阶段一: 环境搭建与仿真验证

**预计时间**: 1-2 周  
**目标**: 在 WSL2 环境下成功编译运行仿真器, 验证 wty-yy RL 运控在仿真器中正常工作

---

## 里程碑

- [ ] WSL2 环境验证通过 (WSLg + NVIDIA)
- [ ] unitree_mujoco 仿真器编译成功并运行
- [ ] wty-yy unitree_cpp_deploy 编译成功
- [ ] 下载并配置 wty-yy 预训练模型
- [ ] 仿真器 + RL 运控联调成功 (狗能走起来)

---

## 详细步骤

### Step 1.1: 验证 WSL2 环境

```bash
# 执行以下命令, 确保环境正常
ls /mnt/wslg              # 应该显示 wslg 相关文件
nvidia-smi                # 应该显示显卡信息
python3 --version         # 应该显示 Python 3.8+
```

### Step 1.2: 安装 MuJoCo

```bash
# 下载 MuJoCo 3.x
cd ~/Downloads
wget https://github.com/google-deepmind/mujoco/releases/download/3.1.0/mujoco-3.1.0-linux-x86_64.tar.gz
tar -xzf mujoco-3.1.0-linux-x86_64.tar.gz
sudo cp -r mujoco-3.1.0 /opt/mujoco

# 添加环境变量
echo 'export MUJOCO_DIR=/opt/mujoco' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$MUJOCO_DIR/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 验证
mujoco --version
```

### Step 1.3: 安装 ROS2 Humble

```bash
# 添加 ROS2 源
sudo locale-gen en_US.UTF-8
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" > /etc/apt/sources.list.d/ros2.list'

# 安装
sudo apt update
sudo apt install -y ros-humble-ros-base ros-humble-rviz2 \
    python3-colcon-common-extensions python3-rosdep

# 初始化
source /opt/ros/humble/setup.bash
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
```

### Step 1.4: 编译 unitree_mujoco 仿真器

```bash
# 安装编译依赖
sudo apt install -y git build-essential cmake libeigen3-dev \
    libboost-all-dev libyaml-cpp-dev libspdlog-dev libfmt-dev

# 编译
cd ~/git/official/unitree_mujoco/simulate
mkdir -p build && cd build
cmake .. && make -j$(nproc)

# 运行测试 (会弹出 MuJoCo 窗口)
./unitree_mujoco
```

### Step 1.5: 编译 wty-yy unitree_cpp_deploy

```bash
# 下载 ONNX Runtime
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/thirdparty
wget https://github.com/microsoft/onnxruntime/releases/download/v1.23.2/onnxruntime-linux-x64-1.23.2.tgz
tar -xzf onnxruntime-linux-x64-1.23.2.tgz

# 编译
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/robots/go2
mkdir -p build && cd build
cmake .. && make -j$(nproc)
```

### Step 1.6: 下载预训练模型

```bash
# 从 Google Drive 下载模型
# 模型链接: https://drive.google.com/drive/folders/1aoXUxw-pGK1MbyzQ4IJzlA_tW8zrWP3Y

# 假设下载到了 ~/Downloads
mkdir -p ~/git/community/wty-yy/unitree_cpp_deploy/logs/go2
cp -r ~/Downloads/go2_moe_cts_self_103.5k_0.6669 ~/git/community/wty-yy/unitree_cpp_deploy/logs/go2/
```

### Step 1.7: 仿真器 + RL 运控联调

```bash
# 终端 1: 启动仿真器
cd ~/git/official/unitree_mujoco/simulate/build
./unitree_mujoco

# 终端 2: 启动 wty-yy 运控 (等待仿真器连接)
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/robots/go2/build
./go2_ctrl -n lo

# 应该看到:
# "Waiting for connection to robot..."
# "Connected to robot."

# 按手柄 (或修改代码使用键盘):
# L2 + A: 站立
# Start + 方向键: 启动 RL 控制
```

### Step 1.8: 验证 RL 运控正常工作

验证指标:
- [ ] 仿真器窗口中狗能站立
- [ ] 按下方向键后狗能移动
- [ ] 移动方向与指令一致
- [ ] 速度正常 (平地约 0.5-1.0 m/s)
- [ ] 无抽搐/异常抖动

---

## 验收标准

| 检查项 | 预期结果 | 验证方法 |
|--------|---------|---------|
| WSL2 WSLg | 窗口能弹出 | 运行 `xeyes` 测试 |
| MuJoCo 仿真器 | 显示机器狗 | 眼睛观察 |
| wty-yy 编译 | 无报错 | 查看编译输出 |
| 模型加载 | 显示模型路径 | 查看日志 |
| RL 站立 | 狗从趴下变为站立 | 眼睛观察 |
| RL 行走 | 狗能沿指令方向移动 | 眼睛观察 |

---

## 产出物

1. 已编译的 `unitree_mujoco` 可执行文件
2. 已编译的 `go2_ctrl` 可执行文件
3. 下载的预训练模型 (ONNX 格式)
4. 验证截图/录屏 (可选)

---

## 下一步

阶段一完成后 → [阶段二: Web 可视化基础](./phase2_visual.md)
