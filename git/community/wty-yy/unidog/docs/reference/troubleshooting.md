# 常见问题与解决方案

## 环境搭建问题

### Q: nvidia-smi 显示 "No devices found"

**原因**: WSL2 未启用 GPU 直通

**解决**:
```powershell
# Windows PowerShell (管理员)
wsl --update
# 如果还是不行, 确保安装了 NVIDIA 驱动 (不是 GeForce Experience)
```

### Q: MuJoCo 窗口不弹出

**原因**: WSLg 未启用 (Windows 10 或旧版 WSL2)

**解决**:
```bash
# 检查 WSLg
ls /mnt/wslg

# 如果不存在, 安装 VcXsrv
# 1. 下载: https://sourceforge.net/projects/vcxsrv/
# 2. 安装时勾选 "Disable access control"
# 3. 启动 XLaunch

# 在 WSL2 中设置
export DISPLAY=$(grep -oP '(?<=nameserver ).+' /etc/resolv.conf):0
```

### Q: ROS2 命令找不到

**原因**: 未 source ROS2 环境

**解决**:
```bash
# 每次新终端都需要
source /opt/ros/humble/setup.bash

# 或永久添加
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
```

---

## 编译问题

### Q: cmake 找不到 MuJoCo

**原因**: MUJOCO_DIR 未设置

**解决**:
```bash
export MUJOCO_DIR=/opt/mujoco
export LD_LIBRARY_PATH=$MUJOCO_DIR/lib:$LD_LIBRARY_PATH
```

### Q: ONNX Runtime 链接失败

**原因**: ONNX Runtime 路径不对

**解决**:
```bash
# 检查 ONNX Runtime 是否存在
ls ~/git/community/wty-yy/unitree_cpp_deploy/deploy/thirdparty/

# 如果下载了, 确认解压后的目录名
```

---

## 仿真器问题

### Q: unitree_mujoco 启动报错 "Cannot connect to simulator"

**原因**: DDS domain_id 不匹配

**解决**:
```bash
# 在仿真器配置中检查 domain_id
cat ~/git/official/unitree_mujoco/simulate/config.yaml
# 确保是 domain_id: 0

# 也可在运行前设置
export CYCLONEDDS_URI='<CycloneDDS><Domain><General><DefaultDomain>0</></></></>'
```

### Q: 仿真器中狗不响应指令

**原因**: go2_ctrl 未连接成功

**解决**:
```bash
# 确认仿真器先运行, 再启动 go2_ctrl
# 终端 1
cd ~/git/official/unitree_mujoco/simulate/build
./unitree_mujoco

# 终端 2
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/robots/go2/build
./go2_ctrl -n lo

# 应该看到: "Connected to robot."
```

---

## 建图问题

### Q: Point-LIO 建图漂移严重

**原因**: 
1. 雷达 FOV 太小 (LIS-3D 70°)
2. 特征点不足
3. IMU 标定不准

**解决**:
1. 降低移动速度
2. 选择特征丰富的环境 (有桌椅等)
3. 考虑升级到 Mid-360 雷达

### Q: OccupancyGrid 显示全黑/全白

**原因**: 地图分辨率或偏移设置不对

**解决**:
```bash
# 检查 Point-LIO 发布的话题
ros2 topic list
ros2 topic echo /map --once
```

---

## 导航问题

### Q: Nav2 规划失败

**原因**: 地图未加载或坐标系不对

**解决**:
```bash
# 确认地图服务器运行
ros2 topic list | grep map

# 查看地图坐标系
ros2 run tf2_ros tf2_echo map base_link
```

### Q: 狗导航时抖动/抽搐

**原因**: 控制频率不稳定

**解决**:
```bash
# 检查 ROS2 实时性
ros2 param get /controller_server use_sim_time

# 使用 CPU 核心隔离
taskset -c 0 ./go2_ctrl -n eth0
```

---

## 真机问题

### Q: SSH 连接 Orin NX 失败

**原因**: IP 不对或网络不通

**解决**:
```bash
# 确认 Orin NX IP (默认 192.168.123.15)
# 用网线直连 PC 和机器狗
ping 192.168.123.15

# 如果 ping 不通, 检查 PC 的以太网 IP
# 应该设置为同一网段, 如 192.168.123.100
```

### Q: 真机运行时关节抽搐

**原因**: 
1. 控制指令冲突 (官方服务未关)
2. PD 参数不对
3. 通信延迟

**解决**:
1. App 中关闭 mcf/* 服务
2. 检查 config.yaml 中的 kp/kd
3. 检查网络延迟, 使用有线以太网

---

## Web 可视化问题

### Q: WebSocket 连接失败

**原因**: IP 地址不对

**解决**:
```bash
# 浏览器端连接的应该是服务端的 IP
# 如果 WebSocket Bridge 在 Orin NX 上运行
# 浏览器应访问: ws://192.168.123.15:8765

# 如果在本地 WSL2
# 访问: ws://localhost:8765
```

### Q: 点云渲染卡顿

**原因**: 数据量太大

**解决**:
```javascript
// 减少渲染点数
const MAX_POINTS = 12000;  // 原来可能是 24000

// 或降低更新频率
const UPDATE_INTERVAL = 100;  // ms
```
