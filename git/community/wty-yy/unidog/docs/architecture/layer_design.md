# 分层设计详解

## Layer 0: 硬件抽象层 (Hardware Abstraction)

### 硬件接口规格

```
┌─────────────────────────────────────────────────────────┐
│  Unitree Go2-edu 硬件配置                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  板载计算: NVIDIA Orin NX 8GB                    │   │
│  │  - CPU: 6-core ARM Cortex-A78AE                 │   │
│  │  - GPU: NVIDIA Ampere (1024 CUDA cores)         │   │
│  │  - RAM: 8GB LPDDR5                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  雷达: Livox LIS-3D (标配) / Mid-360 (可选)    │   │
│  │  - LIS-3D: 70° HFOV, 57° VFOV, 24k pts/s    │   │
│  │  - Mid-360: 360° HFOV, 59° VFOV, 100k pts/s  │   │
│  │  - 接口: Ethernet UDP                           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  12 自由度关节:                                 │   │
│  │  - 3 DOF × 4 腿 = 12 个关节                   │   │
│  │  - 每个关节含电机+编码器                        │   │
│  │  - 控制频率: 500Hz                             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  IMU: 胸部 IMU                                  │   │
│  │  - 3轴陀螺仪 + 3轴加速度计                      │   │
│  │  - 频率: 1000Hz                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### LowState 数据结构

```cpp
// unitree_sdk2 的 LowState 包含的关键数据
struct LowState {
    uint32_t tick;              // 时间戳
    imu_t imu;                  // IMU 数据
    // imu. quaternion[4]       // 四元数 (姿态)
    // imu. gyro[3]              // 角速度
    // imu. accelerometer[3]    // 加速度
    
    motor_state_t motorState[20]; // 电机状态
    // motorState[i].q          // 关节角度 (rad)
    // motorState[i].dq         // 关节角速度 (rad/s)
    // motorState[i].ddq        // 关节角加速度
    
    uint8_t level_flag;         // 控制层级标志
    uint8_t gait_type;          // 步态类型
};
```

### LowCmd 数据结构

```cpp
// 发送控制指令到关节
struct LowCmd {
    motor_cmd_t motorCmd[20];   // 电机指令
    // motorCmd[i].q             // 目标关节角度
    // motorCmd[i].dq           // 目标关节角速度
    // motorCmd[i].tau          // 目标力矩
    // motorCmd[i].kp           // 比例增益
    // motorCmd[i].kd           // 微分增益
};
```

---

## Layer 1: 运控执行层 (Locomotion Layer)

### wty-yy RL 控制器架构

```
                    ┌─────────────────────────────────────┐
                    │      unitree_cpp_deploy            │
                    │                                     │
                    │  ┌───────────────────────────────┐  │
                    │  │       FSM State Machine       │  │
                    │  │                               │  │
                    │  │  ┌─────────┐ ┌───────────┐  │  │
                    │  │  │ 待机     │ │ 固定站立   │  │  │
                    │  │  │Passive  │ │ FixStand  │  │  │
                    │  │  └────┬────┘ └─────┬─────┘  │  │
                    │  │       │            │        │  │
                    │  │       └──────┬─────┘        │  │
                    │  │              ▼               │  │
                    │  │  ┌───────────────────────┐  │  │
                    │  │  │   RL Control (MoE)    │  │  │
                    │  │  │  速度指令 ──► 关节力矩 │  │  │
                    │  │  └───────────┬───────────┘  │  │
                    │  │              │              │  │
                    │  │              ▼              │  │
                    │  │  ┌───────────────────────┐  │  │
                    │  │  │   PD Controller      │  │  │
                    │  │  │   关节角度 ──► 力矩   │  │  │
                    │  │  └───────────┬───────────┘  │  │
                    │  └──────────────┼──────────────┘  │
                    └─────────────────┼─────────────────┘
                                      │ LowCmd (500Hz)
                                      ▼
                              ┌──────────────┐
                              │ 12个关节电机  │
                              │ 执行力矩指令   │
                              └──────────────┘

输入接口:
  - /lowstate (DDS) ← 关节角度, 角速度, IMU
  - /joystick (DDS) ← 手柄遥控 (或来自 Nav2 的 /cmd_vel)

输出接口:
  - /lowcmd (DDS) → 目标力矩 → 电机驱动
```

### 预训练模型列表

| 模型名称 | 架构 | 综合得分 | 适用场景 | 下载链接 |
|---------|------|---------|---------|---------|
| go2_moe_cts | MoE+CTS | 0.6713 | 通用冠军模型 | Google Drive |
| go2_ac_moe_cts | AC-MoE+CTS | 0.6509 | 通用 | Google Drive |
| go2_moe_ng_cts | MoE+NG+CTS | 0.6519 | 通用 | Google Drive |
| go2_mcp_cts | MCP+CTS | 0.6399 | 多策略 | Google Drive |

---

## Layer 2: 建图与感知层 (Perception Layer)

### Point-LIO 建图流程

```
┌─────────────────────────────────────────────────────────┐
│                   Point-LIO 建图流程                      │
└─────────────────────────────────────────────────────────┘

雷达原始点云
(UDP, ~24k pts/s)
      │
      ▼
┌─────────────────┐
│  点云预处理       │ ← 去除近处噪点, 运动畸变补偿
│  Preprocessing   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  特征提取        │ ← 提取边缘特征点和平面特征点
│  Feature Extract │   (iGauss, 动态阈值)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  状态预测        │ ← IMU 预积分预测
│  Predict (EKF)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  特征匹配        │ ← 当前帧特征 vs 地图特征
│  Feature Match   │   (KD-Tree 最近邻搜索)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  状态更新        │ ← 扩展卡尔曼滤波更新
│  Update (EKF)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  地图更新        │ ← 滑窗优化, 点云亚像素插值
│  Map Update     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  输出            │
│  - Odometry     │ ← 狗的位姿 (x, y, z, roll, pitch, yaw)
│  - PointCloud   │ ← 地图点云 (.pcd)
│  - OccupancyGrid│ ← 2D 栅格地图 (Nav2 用)
└─────────────────┘
```

### OccupancyGrid 地图规格

```yaml
# Nav2 地图配置
image: map.pgm
resolution: 0.05  # 5cm/像素
origin: [0.0, 0.0, 0.0]
negate: 0
occupied_thresh: 0.65  # 占用阈值
free_thresh: 0.196     # 空闲阈值
```

---

## Layer 3: 导航规划层 (Navigation Layer)

### Nav2 规划器配置

```
┌─────────────────────────────────────────────────────────┐
│              Nav2 导航堆栈架构                            │
└─────────────────────────────────────────────────────────┘

              ┌─────────────────┐
              │  目标点设定       │
              │ setGoal / RViz  │
              └────────┬────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │    Global Planner        │
         │    (全局路径规划)         │
         │    NavFn / SMAC         │
         └────────────┬────────────┘
                      │
                      │ 全局路径 (Path)
                      ▼
         ┌─────────────────────────┐
         │    Controller           │
         │    (轨迹跟踪)            │
         │    DWB / TEB            │
         │    局部路径优化           │
         └────────────┬────────────┘
                      │
                      │ /cmd_vel (Twist)
                      ▼
         ┌─────────────────────────┐
         │    Collision Avoidance   │
         │    (实时避障)            │
         │    DWA / TEB            │
         │    雷达数据响应           │
         └────────────┬────────────┘
                      │
                      │ /modified_cmd_vel
                      ▼
              ┌───────────────┐
              │  wty-yy C++   │ ← RL 运控层
              │  RL Inference  │
              └───────────────┘
```

---

## Layer 4 & 5: 交互层 (Interaction Layer)

### MCP Server 工具定义

```python
# MCP Server 暴露给 LLM 的工具
TOOLS = [
    {
        "name": "navigate_to",
        "description": "让机器狗自主导航到指定坐标点",
        "parameters": {
            "x": "float: X 坐标 (米)",
            "y": "float: Y 坐标 (米)",
            "yaw": "float: 目标朝向角度 (弧度), 默认 0"
        }
    },
    {
        "name": "set_velocity",
        "description": "直接设置机器狗的移动速度",
        "parameters": {
            "vx": "float: 前进速度 (m/s)",
            "vy": "float: 侧向速度 (m/s), 通常 0",
            "omega": "float: 转向角速度 (rad/s)"
        }
    },
    {
        "name": "get_robot_state",
        "description": "获取机器狗当前状态",
        "returns": {
            "battery": "int: 电量百分比",
            "position": "dict: 当前坐标 (x, y, z)",
            "velocity": "dict: 当前速度 (vx, vy, omega)",
            "posture": "str: 当前姿态 (standing, walking, sitting)"
        }
    },
    {
        "name": "trigger_action",
        "description": "触发预设动作",
        "parameters": {
            "action": "str: 动作名称 (stand_up, sit_down, jump, stop)"
        }
    },
    {
        "name": "emergency_stop",
        "description": "紧急停止 (最高优先级)"
    }
]
```

---

## 分层通信协议

| 层级间通信 | 协议 | 频率 | 说明 |
|-----------|------|------|------|
| Layer 0 ↔ Layer 1 | DDS (CycloneDDS) | 500Hz | LowState/LowCmd |
| Layer 1 ↔ Layer 2 | DDS | 10-20Hz | Odometry 反馈 |
| Layer 2 ↔ Layer 3 | DDS | 10Hz | Odometry + PointCloud |
| Layer 3 ↔ Layer 4 | DDS | 10Hz | /cmd_vel |
| Layer 4 ↔ Layer 5 | WebSocket | 异步 | 状态上报/指令下发 |
| Layer 5 ↔ LLM API | HTTP | 异步 | 自然语言理解 |
