# 阶段三: 遥控 + 建图功能

**预计时间**: 2 周  
**目标**: 实现网页遥控狗行走 + 实时 Point-LIO 建图 + 地图保存加载

---

## 里程碑

- [ ] 雷达数据接入 Point-LIO 建图
- [ ] 遥控指令从网页 → ROS2 → wty-yy C++
- [ ] OccupancyGrid 实时生成
- [ ] 地图保存 (PGM + YAML)
- [ ] 地图加载 (恢复已探索环境)
- [ ] 端到端遥控建图流程跑通

---

## 详细步骤

### Step 3.1: 安装 Point-LIO

```bash
# 创建 ROS2 工作空间
mkdir -p ~/git/ros2_ws/src
cd ~/git/ros2_ws/src

# 克隆 Point-LIO (根据实际雷达型号选择)
git clone https://github.com/hku-mars/point_lio.git

# 安装依赖
sudo apt install -y libpcl-dev

# 编译
cd ~/git/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select point_lio
source install/setup.bash
```

### Step 3.2: 配置 Point-LIO

创建配置文件: `~/git/ros2_ws/src/point_lio/config/livox_lisar.yaml`

```yaml
point_lio:
  ros__parameters:
    # 雷达参数 (LIS-3D)
    lidar_type: Livox
    livox_lidar:
      bd_id: 0
      extrinsic_trans: [0.0, 0.0, 0.0]
      extrinsic_euler: [0.0, 0.0, 0.0]
    
    # 建图参数
    scan_line: 6
    map_resolution: 0.05
    
    # 发布频率
    publish_freq: 10.0
    
    # 点云处理
    point_filter_num: 2
    max_iteration: 3
```

### Step 3.3: 启动雷达建图

```bash
# 终端 1: 启动 Point-LIO
cd ~/git/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch point_lio point_lio.launch.py

# 终端 2: 查看建图输出
ros2 topic list
# 应该看到: /odom, /map, /map_points, /path
```

### Step 3.4: 修改 wty-yy C++ 接入 Nav2 /cmd_vel

当前 wty-yy 只接收手柄输入, 需要修改为同时接收 ROS2 /cmd_vel:

```cpp
// 在 State_RLBase.cpp 中添加 ROS2 订阅

class CmdVelSubscriber {
    rclcpp::Node::SharedPtr node;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr sub;
    geometry_msgs::msg::Twist latest_cmd;
    
public:
    void init() {
        node = rclcpp::Node::make_shared("go2_cmd_vel");
        sub = node->create_subscription<geometry_msgs::msg::Twist>(
            "/cmd_vel",
            10,
            [this](const geometry_msgs::msg::Twist::SharedPtr msg) {
                latest_cmd = *msg;
            }
        );
    }
    
    void spin() {
        rclcpp::spin_some(node);
    }
    
    geometry_msgs::msg::Twist getCmd() {
        return latest_cmd;
    }
};
```

### Step 3.5: 打通遥控链路

```
遥控指令链路:
网页方向杆
    ↓ WebSocket
WebSocket Bridge
    ↓ ROS2 /cmd_vel (Twist)
wty-yy C++ go2_ctrl
    ↓ RL 推理
LowCmd (500Hz)
    ↓ DDS
unitree_mujoco / 真实电机
    ↓
机器狗移动
```

### Step 3.6: 地图保存功能

```python
# 在 WebSocket Bridge 中添加地图保存

def save_map(grid_msg: OccupancyGrid):
    # 保存 PGM 图片
    import numpy as np
    from PIL import Image
    
    data = np.array(grid_msg.data).reshape(grid_msg.info.height, grid_msg.info.width)
    
    # 转换为 PGM 格式 (0=黑色占用, 255=白色空闲, 128=灰色未知)
    pgm_data = np.where(data == 2, 0, np.where(data == 1, 255, 128)).astype(np.uint8)
    
    img = Image.fromarray(pgm_data)
    img.save('map.pgm')
    
    # 保存 YAML 配置
    yaml_content = f"""
image: map.pgm
resolution: {grid_msg.info.resolution}
origin: [{grid_msg.info.origin.position.x}, {grid_msg.info.origin.position.y}, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""
    with open('map.yaml', 'w') as f:
        f.write(yaml_content)
```

### Step 3.7: 端到端测试

```bash
# 1. 启动仿真器
cd ~/git/official/unitree_mujoco/simulate/build
./unitree_mujoco

# 2. 启动 wty-yy 运控
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/robots/go2/build
./go2_ctrl -n lo

# 3. 启动 WebSocket Bridge
cd ~/git/community/unidog_ws
python3 websocket_bridge/bridge.py

# 4. 打开浏览器
# 访问 http://localhost:8080

# 5. 切换到建图模式
# 用方向杆遥控狗走一圈

# 6. 保存地图
# 点击 "💾 保存地图"
```

---

## 验收标准

| 检查项 | 预期结果 | 验证方法 |
|--------|---------|---------|
| Point-LIO 运行 | 无报错 | 终端输出 |
| /odom 输出 | 有位姿数据 | `ros2 topic echo /odom` |
| OccupancyGrid | 有地图数据 | 网页 2D 地图 |
| 网页遥控 | 狗响应指令移动 | 眼睛观察 |
| 地图保存 | 生成 map.pgm + map.yaml | 文件系统 |
| 地图加载 | 恢复之前探索的地图 | 网页显示 |

---

## 下一步

阶段三完成后 → [阶段四: 导航+避障](./phase4_nav.md)
