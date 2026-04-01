# 环境搭建指南

## WSL2 环境验证

### 检查当前环境

```bash
# 1. 确认 WSL2 版本
uname -r
# 应该显示类似: 5.15.153.1-microsoft-standard-WSL2

# 2. 确认 WSLg 是否启用
ls /mnt/wslg
# 如果存在目录, 说明 WSLg 已启用

# 3. 检查 NVIDIA 驱动
nvidia-smi
# 如果看到显卡信息, 说明 GPU 直通正常

# 4. 检查 Ubuntu 版本
cat /etc/os-release
# 应该是 Ubuntu 22.04 LTS
```

### Windows WSL2 配置文件

在 Windows 上打开 PowerShell (管理员), 创建/编辑 `C:\Users\<用户名>\.wslconfig`:

```ini
[wsl2]
memory=12GB
processors=6
nestedTabs=true
localhostForwarding=true
```

修改后重启 WSL:
```powershell
wsl --shutdown
# 重新打开 WSL2 终端即可
```

---

## 安装 MuJoCo

```bash
# 1. 下载 MuJoCo
cd ~/Downloads
wget https://github.com/google-deepmind/mujoco/releases/download/3.1.0/mujoco-3.1.0-linux-x86_64.tar.gz
tar -xzf mujoco-3.1.0-linux-x86_64.tar.gz

# 2. 安装到系统目录
sudo cp -r mujoco-3.1.0 /opt/mujoco
sudo ln -s /opt/mujoco/bin/mujoco /usr/local/bin/mujoco

# 3. 添加环境变量
echo 'export MUJOCO_DIR=/opt/mujoco' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$MUJOCO_DIR/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 4. 验证安装
mujoco --version
```

---

## 安装 ROS2 Humble

```bash
# 1. 设置 locale
sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8

# 2. 添加 ROS2 源
sudo apt update
sudo apt install -y curl gnupg lsb-release
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" > /etc/apt/sources.list.d/ros2.list'

# 3. 安装 ROS2
sudo apt update
sudo apt install -y ros-humble-ros-base ros-humble-rviz2 \
    ros-humble-robot-localization \
    ros-humble-navigation2 ros-humble-nav2-bringup \
    python3-colcon-common-extensions python3-rosdep

# 4. 初始化 ROS2
source /opt/ros/humble/setup.bash
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc

# 5. 安装额外依赖
sudo apt install -y python3-pip libeigen3-dev libboost-all-dev \
    libyaml-cpp-dev libspdlog-dev

# 6. 验证安装
source /opt/ros/humble/setup.bash
ros2 doctor
```

---

## 编译 unitree_mujoco

```bash
# 1. 准备目录
mkdir -p ~/git/workspace
cd ~/git/workspace

# 2. 安装依赖
sudo apt install -y git build-essential cmake

# 3. 编译仿真器
cd ~/git/official/unitree_mujoco/simulate
mkdir -p build && cd build
cmake .. && make -j$(nproc)

# 4. 运行仿真器测试
./unitree_mujoco
# 应该弹出 MuJoCo 窗口
```

---

## 编译 wty-yy/unitree_cpp_deploy

```bash
# 1. 安装编译依赖
sudo apt install -y libboost-program-options-dev libyaml-cpp-dev \
    libeigen3-dev libfmt-dev libspdlog-dev

# 2. 下载 ONNX Runtime (Linux x64)
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/thirdparty
wget https://github.com/microsoft/onnxruntime/releases/download/v1.23.2/onnxruntime-linux-x64-1.23.2.tgz
tar -xzf onnxruntime-linux-x64-1.23.2.tgz

# 3. 编译
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/robots/go2
mkdir -p build && cd build
cmake .. && make -j$(nproc)

# 4. 下载预训练模型 (如果还没有)
# 从 Google Drive 下载 go2_moe_cts 模型
# 解压到 ~/git/community/wty-yy/unitree_cpp_deploy/logs/go2/

# 5. 测试运行 (连接仿真器)
./go2_ctrl -n lo
# 按 L2 + A 站立, 按 Start + 方向键启动 RL 控制
```

---

## 安装 Python Web 开发环境

```bash
# 1. 安装 Python 3.10+
python3 --version

# 2. 安装 pip
sudo apt install -y python3-pip python3-venv

# 3. 创建虚拟环境 (可选)
python3 -m venv ~/venv/unidog
source ~/venv/unidog/bin/activate

# 4. 安装 Web 依赖
pip install websockets numpy transforms3d
pip install rclpy  # ROS2 Python 包 (需要 source /opt/ros/humble/setup.bash)

# 5. 安装前端工具 (Node.js)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g pnpm
```

---

## 创建 UniDog 工作区

```bash
# 1. 创建项目目录
mkdir -p ~/git/community/unidog_ws
cd ~/git/community/unidog_ws

# 2. 创建子目录
mkdir -p websocket_bridge mcp_server web

# 3. 初始化 Web 项目
cd web
pnpm create vite@latest . --template vue-ts
pnpm install
pnpm add three @types/three nipplejs

# 4. 目录结构
tree -L 2 ~/git/community/unidog_ws
```

---

## 验证清单

完成环境搭建后, 运行以下命令验证:

```bash
# 验证 WSLg
glxinfo | head -5

# 验证 NVIDIA
nvidia-smi

# 验证 MuJoCo
mujoco --version

# 验证 ROS2
source /opt/ros/humble/setup.bash
ros2 topic list  # 应该显示空的 topic 列表

# 验证 unitree_mujoco
cd ~/git/official/unitree_mujoco/simulate/build
./unitree_mujoco  # 弹出窗口

# 验证 wty-yy C++ (需要先运行仿真器)
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/robots/go2/build
./go2_ctrl -n lo  # 连接仿真器
```

---

## 常见问题

### Q: nvidia-smi 显示 "No devices found"

A: 确保在 Windows 上安装了 NVIDIA 驱动, 并且 WSL2 使用的是 WSLg:
```powershell
# 在 PowerShell (管理员) 中
wsl --update
```

### Q: MuJoCo 窗口不弹出

A: 检查 WSLg 是否启用:
```bash
ls /mnt/wslg
# 如果不存在, 可能是 Windows 10, 需要安装 VcXsrv
```

### Q: ROS2 找不到包

A: 确保 source 了 ROS2 环境:
```bash
source /opt/ros/humble/setup.bash
```
