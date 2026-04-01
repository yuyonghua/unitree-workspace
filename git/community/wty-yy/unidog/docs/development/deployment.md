# 真机部署指南

## 从仿真迁移到真机

仿真环境验证通过后, 将代码迁移到真实 Go2 机器狗上。

---

## 准备工作

### 硬件准备

| 物品 | 说明 |
|------|------|
| Unitree Go2-edu | 真实机器狗 |
| 以太网网线 | 连接 Orin NX 和开发 PC |
| 稳压电源 | 12V 5A 以上 |
| 电脑 | 运行 WSL2 的 Windows PC |

### 网络配置

```bash
# 1. 设置固定 IP (Windows 端)
# 控制面板 → 网络 → 以太网 → 属性 → IPv4
# 设置为: 192.168.123.100

# 2. Orin NX 端 (机器狗内置)
# 默认 IP: 192.168.123.15
# 可以在 /etc/netplan/ 中修改

# 3. 测试连通性
ping 192.168.123.15
```

---

## 真机编译

### 在 Orin NX 上编译 wty-yy C++

```bash
# 1. SSH 到 Orin NX (需要一根网线连接 PC 和机器狗)
ssh unitree@192.168.123.15
# 默认密码: unitree

# 2. 安装编译依赖
sudo apt update
sudo apt install -y git build-essential cmake \
    libboost-program-options-dev libyaml-cpp-dev \
    libeigen3-dev libfmt-dev libspdlog-dev

# 3. 克隆代码
mkdir -p ~/git
cd ~/git
git clone https://github.com/wty-yy/unitree_cpp_deploy.git
git clone https://github.com/unitreerobotics/unitree_sdk2.git

# 4. 下载 ONNX Runtime (Orin NX aarch64)
cd ~/unitree_cpp_deploy/deploy/thirdparty
wget https://github.com/csukuangfj/onnxruntime-libs/releases/download/v1.16.0/onnxruntime-linux-aarch64-gpu-1.16.0.tar.bz2
tar -xjf onnxruntime-linux-aarch64-gpu-1.16.0.tar.bz2

# 5. 编译
cd ~/unitree_cpp_deploy/deploy/robots/go2
mkdir -p build && cd build
cmake .. && make -j4

# 6. 复制预训练模型
mkdir -p ~/logs/go2
# 从 PC 拷贝模型到 Orin NX
scp -r ~/git/community/wty-yy/unitree_cpp_deploy/logs/go2/* \
    unitree@192.168.123.15:~/logs/go2/
```

---

## 真机配置

### 关闭官方运控服务

**重要**: 必须在机器狗 App 上关闭官方运控服务, 避免冲突!

```bash
# 在机器狗 App 上操作:
# 1. 连接机器狗 WiFi
# 2. 打开宇树 App
# 3. 设置 → 服务状态
# 4. 关闭 mcf/* 相关服务
# 5. 关闭官方控制程序
```

### ROS2 环境配置 (Orin NX)

```bash
# 1. 安装 ROS2 Humble (Orin NX)
# 参考: https://docs.ros.org/en/humble/Installation/Ubuntu-Install.html

# 2. 安装 Point-LIO
cd ~/git
git clone https://github.com/hku-mars/point_lio.git
cd point_lio
mkdir build && cd build
cmake .. && make -j4

# 3. 安装 Nav2
sudo apt install -y ros-humble-navigation2 ros-humble-nav2-bringup
```

---

## 真机运行

### 启动顺序

```bash
# 终端 1: 机器狗站立准备
# 打开机器狗电源, 等待自检完成
# 按 L2 + A 站立

# 终端 1: 启动雷达驱动
source ~/ros2_ws/install/setup.bash
ros2 launch livox_ros_driver2 livox_lidar.launch.py

# 终端 2: 启动 Point-LIO 建图
source ~/ros2_ws/install/setup.bash
ros2 launch point_lio point_lio.launch.py

# 终端 3: 启动 wty-yy RL 运控
cd ~/unitree_cpp_deploy/deploy/robots/go2/build
sudo ./go2_ctrl -n eth0  # eth0 是机器狗内部网卡
# 注意: 真机上需要 sudo 运行, 才能访问实时网络

# 终端 4: 启动 WebSocket Bridge
cd ~/unidog_ws
python3 websocket_bridge/bridge.py

# 终端 5: 启动 Nav2 (如果需要导航)
source ~/ros2_ws/install/setup.bash
ros2 launch nav2_bringup go2_nav.launch.py
```

### 启动后操作

```bash
# 1. 连接成功后应该看到:
# "Connected to robot."

# 2. 按手柄 L2 + A 让狗站立

# 3. 按 Start + 上方向键启动 RL 控制
# 狗开始行走

# 4. 在浏览器中访问
# http://<Orin NX IP>:8080
# 例如: http://192.168.123.15:8080
```

---

## 关键配置

### DDS 网络配置

```xml
<!-- 在 ~/.cyclonedds.xml 中配置 -->
<?xml version="1.0" encoding="UTF-8"?>
<cyclonedds xmlns="http://www.cyclonedds.org">
  <domain id="0">
    <participant>
      <transport_builtin>
        <udpv4>
          <networkInterface address="192.168.123.0/24"/>
        </udpv4>
      </transport_builtin>
    </participant>
  </domain>
</cyclonedds>
```

### CPU 核心隔离 (实时性保障)

```bash
# 在 /etc/default/grub 中添加
GRUB_CMDLINE_LINUX_DEFAULT="isolcpus=0,1,2,3 rcu_nocbs=0,1,2,3"
# 然后 sudo update-grub && sudo reboot

# 运行 wty-yy 时绑定核心
sudo taskset -c 0,1 ./go2_ctrl -n eth0

# 使用实时调度
sudo chrt -f 99 ./go2_ctrl -n eth0
```

---

## 调试与排错

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 连接失败 | IP 不通 | 检查网线, ping 确认 |
| 狗不响应 | 官方服务未关闭 | App 中关闭 mcf/* |
| 抽搐/抖动 | 控制频率不对 | 检查 DDS domain_id |
| 建图漂移大 | 雷达型号不对 | 确认是 LIS-3D 还是 Mid-360 |
| 导航走偏 | 定位不准 | 校准 EKF 参数 |

### 调试命令

```bash
# 查看 DDS Topic
ros2 topic list

# 查看实时数据
ros2 topic echo /odom --once
ros2 topic hz /utlidar/cloud

# 查看节点关系
rqt_graph

# 查看 ROS2 通信质量
ros2 doctor
```
