#!/bin/bash
#===============================================================================
# UniDog 环境一键安装脚本
# 用于 WSL2 Ubuntu 22.04
# 
# 使用方法:
#   chmod +x setup_env.sh
#   ./setup_env.sh
#===============================================================================

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  UniDog 环境安装脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 WSL2
check_wsl() {
    echo -e "${YELLOW}[1/8] 检查 WSL2 环境...${NC}"
    if grep -qi microsoft /proc/version; then
        echo -e "${GREEN}✓ WSL2 检测通过${NC}"
    else
        echo -e "${RED}✗ 请在 WSL2 中运行此脚本${NC}"
        exit 1
    fi
}

# 安装系统依赖
install_system_deps() {
    echo -e "${YELLOW}[2/8] 安装系统依赖...${NC}"
    sudo apt update
    sudo apt install -y \
        build-essential \
        cmake \
        git \
        wget \
        curl \
        locales \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        libeigen3-dev \
        libboost-all-dev \
        libyaml-cpp-dev \
        libfmt-dev \
        libspdlog-dev \
        libpcl-dev \
        libgl1-mesa-dev \
        libx11-dev \
        libxrandr-dev \
        libxinerama-dev \
        libxcursor-dev \
        libxi-dev \
        x11-apps
    echo -e "${GREEN}✓ 系统依赖安装完成${NC}"
}

# 安装 MuJoCo
install_mujoco() {
    echo -e "${YELLOW}[3/8] 安装 MuJoCo...${NC}"
    
    MUJOCO_DIR="/opt/mujoco"
    if [ -d "$MUJOCO_DIR" ]; then
        echo -e "${GREEN}MuJoCo 已安装${NC}"
    else
        cd ~/Downloads
        wget -q https://github.com/google-deepmind/mujoco/releases/download/3.1.0/mujoco-3.1.0-linux-x86_64.tar.gz
        sudo tar -xzf mujoco-3.1.0-linux-x86_64.tar.gz -C /opt
        sudo ln -sf /opt/mujoco-3.1.0/bin/mujoco /usr/local/bin/mujoco
        rm mujoco-3.1.0-linux-x86_64.tar.gz
        echo 'export MUJOCO_DIR=/opt/mujoco' >> ~/.bashrc
        echo 'export LD_LIBRARY_PATH=$MUJOCO_DIR/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
        echo -e "${GREEN}✓ MuJoCo 安装完成${NC}"
    fi
}

# 安装 ROS2 Humble
install_ros2() {
    echo -e "${YELLOW}[4/8] 安装 ROS2 Humble...${NC}"
    
    if [ -d "/opt/ros/humble" ]; then
        echo -e "${GREEN}ROS2 Humble 已安装${NC}"
    else
        # 设置 locale
        sudo locale-gen en_US.UTF-8
        export LANG=en_US.UTF-8
        
        # 添加 ROS2 源
        curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
        sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" > /etc/apt/sources.list.d/ros2.list'
        
        # 安装
        sudo apt update
        sudo apt install -y \
            ros-humble-ros-base \
            ros-humble-rviz2 \
            ros-humble-robot-localization \
            ros-humble-navigation2 \
            ros-humble-nav2-bringup \
            python3-colcon-common-extensions \
            python3-rosdep \
            python3-vcstool
            
        # 初始化
        sudo rosdep init
        echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
        echo -e "${GREEN}✓ ROS2 Humble 安装完成${NC}"
    fi
}

# 安装 Python 依赖
install_python_deps() {
    echo -e "${YELLOW}[5/8] 安装 Python 依赖...${NC}"
    
    pip3 install --upgrade pip
    pip3 install \
        numpy \
        scipy \
        matplotlib \
        opencv-python \
        websockets \
        transforms3d \
        pillow \
        pyyaml
        
    echo -e "${GREEN}✓ Python 依赖安装完成${NC}"
}

# 安装 Node.js 和 pnpm
install_nodejs() {
    echo -e "${YELLOW}[6/8] 安装 Node.js...${NC}"
    
    if command -v node &> /dev/null; then
        echo -e "${GREEN}Node.js 已安装: $(node --version)${NC}"
    else
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt install -y nodejs
        npm install -g pnpm
        echo -e "${GREEN}✓ Node.js 安装完成${NC}"
    fi
}

# 创建工作目录
create_workspace() {
    echo -e "${YELLOW}[7/8] 创建工作目录...${NC}"
    
    mkdir -p ~/git/community/unidog_ws/{websocket_bridge,mcp_server,web}
    mkdir -p ~/git/ros2_ws/src
    
    echo -e "${GREEN}✓ 工作目录创建完成${NC}"
}

# 验证安装
verify_install() {
    echo -e "${YELLOW}[8/8] 验证安装...${NC}"
    
    echo -n "MuJoCo: "
    mujoco --version || echo -e "${RED}未安装${NC}"
    
    echo -n "ROS2: "
    if [ -f "/opt/ros/humble/setup.bash" ]; then
        echo -e "${GREEN}已安装${NC}"
    else
        echo -e "${RED}未安装${NC}"
    fi
    
    echo -n "Python: "
    python3 --version
    
    echo -n "Node.js: "
    node --version || echo -e "${RED}未安装${NC}"
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo -e "  环境安装完成!"
    echo -e "==========================================${NC}"
    echo ""
    echo "下一步:"
    echo "  1. 编译 unitree_mujoco 仿真器"
    echo "  2. 编译 wty-yy unitree_cpp_deploy"
    echo "  3. 参考 docs/development/phases/ 开始开发"
}

# 运行安装流程
check_wsl
install_system_deps
install_mujoco
install_ros2
install_python_deps
install_nodejs
create_workspace
verify_install
