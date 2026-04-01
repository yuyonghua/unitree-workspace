# 模块规格说明

## 模块清单与依赖关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UniDog 模块依赖图                                  │
└─────────────────────────────────────────────────────────────────────────┘

                          ┌─────────────────────┐
                          │  UniDog Web (前端)  │
                          │  Vue3 + Three.js   │
                          └──────────┬──────────┘
                                     │ WebSocket
                          ┌──────────▼──────────┐
                          │  WebSocket Bridge   │
                          │  Python asyncio     │
                          └──────────┬──────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           │                         │                         │
    ┌──────▼──────┐          ┌──────▼──────┐          ┌──────▼──────┐
    │  MCP Server │          │  Nav2       │          │  Point-LIO  │
    │  Python     │          │  ROS2       │          │  ROS2       │
    └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
           │                         │                         │
           │                         │ /cmd_vel               │ /odom
           │                         ▼                         │
    ┌──────▼──────────────────────────────────────────────────────────┐
    │                      wty-yy C++ (go2_ctrl)                     │
    │                      RL 运控 + ONNX 推理                        │
    └──────┬──────────────────────────────────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │  LowCmd      │
    │  (500Hz)     │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  Unitree     │
    │  Motor       │
    └──────────────┘
```

---

## 模块 1: unitree_mujoco (仿真器)

### 基本信息

| 属性 | 值 |
|------|-----|
| 路径 | `git/official/unitree_mujoco/simulate` |
| 语言 | C++17 |
| 依赖 | MuJoCo 3.x, unitree_sdk2, CycloneDDS |
| 用途 | 物理仿真，无需真机即可开发 |

### 接口规格

```cpp
// 订阅 DDS Topic
/subscriber/lowstate    // 接收关节状态 (用于验证发送的指令)

// 发布 DDS Topic
/publisher/lowcmd       // 发布关节控制指令

// 配置文件
simulate/config.yaml
  - domain_id: 0        // DDS 域ID
  - use_joystick: 1    // 启用手柄
  - robot_type: go2     // 机器人型号
```

### 编译与运行

```bash
cd git/official/unitree_mujoco/simulate
mkdir build && cd build
cmake .. && make -j$(nproc)

# 运行仿真器
./unitree_mujoco

# WSL2 下会自动弹出 MuJoCo 窗口 (WSLg)
```

---

## 模块 2: wty-yy/unitree_cpp_deploy (运控)

### 基本信息

| 属性 | 值 |
|------|-----|
| 路径 | `git/community/wty-yy/unitree_cpp_deploy` |
| 语言 | C++17 |
| 依赖 | unitree_sdk2, ONNXRuntime, Boost, yaml-cpp |
| 模型格式 | ONNX (.onnx) |
| 控制频率 | 500Hz (PD) + 50Hz (NN) |

### 接口规格

```cpp
// DDS 接口
/subscriber/lowstate    // 订阅关节状态
/publisher/lowcmd       // 发布控制指令

// 网络配置
-n, --network <iface>   // 指定网卡名, 如 lo, eth0, wlan0

// 日志配置
--log                   // 启用日志记录

// 配置文件
deploy/robots/go2/config/config.yaml
  - Velocity_Up.policy_dir: ../../../logs/go2/go2_moe_cts
  - Velocity.fixed_command.enabled: true
  - Velocity.logging: true
```

### 运控状态机

```cpp
enum class FSMState {
    PASSIVE,      // 待机, 电机卸力
    FIXED_STAND,  // 固定站立 (按住当前姿态)
    RL_CONTROL,   // RL 运控 (速度指令模式)
    FIXED_CMD,    // 固定指令模式
    DAMPING       // 阻尼模式 (软着陆)
};

// 切换方式 (手柄或代码)
PASSIVE       → FIXED_STAND:  按 L2 + A
FIXED_STAND   → RL_CONTROL:   按 Start + 方向键
RL_CONTROL    → DAMPING:      按 L2 + B
任意状态      → PASSIVE:      紧急停止
```

---

## 模块 3: WebSocket Bridge (Web 通信中枢)

### 基本信息

| 属性 | 值 |
|------|-----|
| 路径 | `git/community/unidog_ws/websocket_bridge` |
| 语言 | Python 3.10+ |
| 依赖 | asyncio, websockets, rclpy, numpy, transforms3d |
| 端口 | 8765 (WebSocket), 8080 (HTTP 可选) |

### 订阅的 ROS2 Topic

| Topic | 类型 | 用途 |
|-------|------|------|
| `/utlidar/cloud` | PointCloud2 | 雷达点云 → 转发浏览器 |
| `/odom` | Odometry | 里程计 → 转发浏览器 |
| `/map` | OccupancyGrid | 2D 地图 → PNG 编码 → 浏览器 |
| `/joint_states` | JointState | 关节状态 → 转发浏览器 |
| `/cmd_vel` | Twist | 浏览器指令 → 转发 Nav2 (导航模式) |

### WebSocket API

```python
# 启动服务
python3 websocket_bridge.py --ros2           # 连接本地 ROS2
python3 websocket_bridge.py --host 0.0.0.0 --port 8765

# 浏览器连接
ws://localhost:8765

# 发送遥控指令
{"type": "cmd_vel", "vx": 0.5, "vy": 0.0, "omega": 0.2}

# 接收点云
{"type": "pointcloud", "data": [...], "count": 24000}
```

---

## 模块 4: UniDog Web (前端可视化)

### 基本信息

| 属性 | 值 |
|------|-----|
| 路径 | `git/community/unidog_ws/web` |
| 语言 | TypeScript, HTML, CSS |
| 框架 | Vue 3 + Vite |
| 3D 渲染 | Three.js |
| 2D 渲染 | Canvas 2D |
| 实时通信 | WebSocket |

### 页面模块

| 模块 | 技术 | 说明 |
|------|------|------|
| 2D 地图 | Canvas 2D | OccupancyGrid 实时渲染 |
| 3D 视图 | Three.js | 点云 + 机器狗模型 |
| 方向杆 | nipplejs | 遥控控件 |
| 状态面板 | Vue 组件 | 电池/温度/里程 |
| 模式切换 | Vue Router | 建图/导航/语音模式 |

### 页面布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [建图]  [导航]  [语音]  [设置]                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────┐   ┌────────────────────────────────────┐ │
│  │                          │   │                                    │ │
│  │      3D 可视化窗口        │   │         2D 地图窗口               │ │
│  │   (点云 + 机器狗模型)     │   │     (OccupancyGrid)               │ │
│  │                          │   │                                    │ │
│  │                          │   │                                    │ │
│  │      🐕 (机器狗)         │   │         🐕 (顶视图)                │ │
│  │      ●●● (障碍点云)      │   │         ■■ (障碍物)               │ │
│  │                          │   │         ═══ (已探索路径)            │ │
│  └──────────────────────────┘   └────────────────────────────────────┘ │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  操作面板                                                           │ │
│  │  [▲]  [◀] [●] [▶] [▼]    速度 [━━━━●━━] 0.5m/s                   │ │
│  │  [⏸ 暂停] [📍 目标点] [💾 保存地图] [🗑️ 清除]                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 模块 5: MCP Server (LLM 接口)

### 基本信息

| 属性 | 值 |
|------|-----|
| 路径 | `git/community/unidog_ws/mcp_server` |
| 语言 | Python 3.10+ |
| 框架 | @modelcontextprotocol/sdk |
| 通信 | HTTP (连接 LLM API), DDS (连接 ROS2) |

### 工具定义

```python
TOOLS = [
    "navigate_to(x, y, yaw=0)"      # 自主导航到坐标点
    "set_velocity(vx, vy, omega)"   # 直接设置速度
    "get_robot_state()"             # 获取机器人状态
    "get_location_list()"           # 获取已知位置列表
    "trigger_action(action)"         # 触发预设动作
    "emergency_stop()"              # 紧急停止
]

# System Prompt
SYSTEM_PROMPT = """
你是一个机器狗控制助手, 名字叫小GO。
你可以控制 Unitree Go2 四足机器人, 具备以下能力:
- 自主导航到指定坐标点
- 直接控制移动速度
- 执行预设动作 (站立、坐下、跳跃)
- 实时查询机器人状态

安全规则:
1. 任何情况下, "STOP" 或 "停止" 指令必须立即执行 emergency_stop()
2. 不要让机器狗撞向障碍物
3. 电量低于 20% 时提醒用户

已知位置:
- A点: (5.2, -1.3) # 实验室入口
- B点: (10.0, 0.0) # 服务器机房
- 充电桩: (0.0, 0.0)
"""
```

---

## 模块 6: Point-LIO (建图引擎)

### 基本信息

| 属性 | 值 |
|------|-----|
| 来源 | `point_lio` ROS2 包 |
| 语言 | C++ |
| 依赖 | PCL, Eigen, livox_ros_driver2 |
| 输出 | Odometry, PointCloud, OccupancyGrid |

### 参数配置

```yaml
# point_lio.yaml
point_lio:
  ros__parameters:
    # 雷达参数
    lidar_type: Livox            # LIS-3D / Mid-360
    bdh_id: 0
    publish_freq: 10.0           # Hz
    
    # 建图参数
    scan_line: 6                 # 扫描线数 (LIS-3D)
    mapping: 
      reg_dist: 0.3              # 配准距离阈值
      plane_detect: 0.1         # 平面检测阈值
      
    # 优化参数
    opt:
      max_iterations: 4         # 最大迭代次数
      tolerance: 1e-4          # 收敛阈值
```

---

## 模块依赖矩阵

| 模块 | 依赖模块 | 说明 |
|------|---------|------|
| wty-yy C++ | unitree_sdk2 | DDS 通信 |
| wty-yy C++ | ONNXRuntime | NN 推理 |
| WebSocket Bridge | ROS2 | 订阅雷达/里程计 |
| WebSocket Bridge | websockets | Web 通信 |
| UniDog Web | WebSocket Bridge | 获取数据 |
| MCP Server | WebSocket Bridge | 获取状态 |
| MCP Server | Nav2 | 下发导航目标 |
| Nav2 | Point-LIO | 获取 Odometry |
| Nav2 | wty-yy C++ | 接收 /cmd_vel |
