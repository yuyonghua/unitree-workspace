# Unitree 机器狗巡检相关开源项目汇总

> 整理时间：2026-03-21
> 覆盖领域：建图 (SLAM)、自主导航、避障、爬楼梯、工业巡检
> 适用平台：Go1、Go2、Aliengo、G1、H1

---

## 一、建图 (SLAM)

### 1. OM1 ROS2 SDK (OpenMind)
- **链接**: https://github.com/OpenMind/unitree_go2_ros2_sdk
- **Stars**: 较活跃 (2025年6月创建)
- **支持机器人**: Go2, G1, Tron (LimX)
- **技术栈**: ROS 2 Humble, RPLiDAR, SLAM Toolbox, Nav2, Intel D435i
- **核心功能**:
  - 实时 SLAM（使用 SLAM Toolbox）
  - 3D SLAM 建图
  - Nav2 自主导航
  - AprilTag 视觉对接自动充电
  - Gazebo 仿真环境
- **许可证**: MIT
- **适用场景**: 室内外巡检，需要额外安装 RPLiDAR

### 2. go2_slam (Unitree-Go2-Robot)
- **链接**: https://github.com/Unitree-Go2-Robot/go2_slam
- **Stars**: 2
- **支持机器人**: Go2
- **技术栈**: ROS 2 Humble
- **核心功能**: Go2 SLAM 集成
- **许可证**: Apache 2.0

### 3. unitree-go2-slam-nav2 (Gitee)
- **链接**: https://gitee.com/jhaiq/unitree-go2-slam-nav2
- **作者**: Hossein Naderi
- **支持机器人**: Go2
- **技术栈**: ROS 2, RTAB-Map, Nav2, Intel RealSense, LiDAR
- **核心功能**:
  - 室内外实时建图
  - 传感器融合（RGB-D相机 + LiDAR点云）
  - 自主导航与路径规划
  - 人脸识别功能
- **适用场景**: 巡检中需要识别人脸的场景

### 4. tsinghua-Unitree-ROS (清华大学)
- **链接**: https://github.com/MistyMoonR/tsinghua-Unitree-ROS
- **作者**: 清华大学
- **支持机器人**: A1
- **技术栈**: ROS Melodic, Velodyne-16, Intel D435i, Spatial IMU
- **核心功能**:
  - 多传感器融合 SLAM
  - Velodyne-16 线激光雷达建图
  - RealSense 深度相机集成
- **适用场景**: 学术研究，多传感器SLAM

### 5. exploration_go2 (前沿探索SLAM)
- **链接**: https://github.com/gcairone/exploration_go2
- **作者**: Scuola Superiore Sant'Anna (意大利)
- **支持机器人**: Go2 EDU
- **技术栈**: ROS 2 Foxy, LIO-SAM, Nav2, NVIDIA Jetson
- **核心功能**:
  - 基于前沿的自主探索建图
  - LIO-SAM 3D SLAM（针对 Livox Mid-360 适配）
  - 3D→2D 地图投影
  - Nav2 自主导航
- **适用场景**: 未知环境自主探索巡检

---

## 二、完整自主导航栈 (Full Autonomy Stack)

### 1. autonomy_stack_go2 (CMU 卡内基梅隆大学) ⭐推荐
- **链接**: https://github.com/jizhang-cmu/autonomy_stack_go2
- **作者**: Guofei Chen, Botao He, Guanya Shi, Ji Zhang (CMU)
- **Stars**: 活跃维护 (2024年6月创建, 持续更新至2026年)
- **支持机器人**: Go2
- **技术栈**: ROS 2 (Foxy/Humble), C++, Unity仿真, Point-LIO
- **核心功能**:
  - **仅使用Go2自带L1雷达+IMU**，无需额外传感器
  - 完整 SLAM 模块（基于 Point-LIO）
  - 路径规划器 (Route Planner)
  - 地形可通行性分析 (Terrain Traversability)
  - 碰撞避障 (Collision Avoidance)
  - 航点跟踪 (Waypoint Following)
  - Unity 环境模型仿真
  - 支持真机部署（板载电脑或外接电脑）
- **许可证**: 开源
- **适用场景**: **最推荐的完整导航方案**，无需改装硬件

### 2. go2AutonomousNavigation
- **链接**: https://github.com/Sayantani-Bhattacharya/go2Autonomousnavigation
- **作者**: Sayantani Bhattacharya
- **支持机器人**: Go2
- **技术栈**: ROS 2 Jazzy, C++, RTAB-Map, Nav2, 4D LiDAR
- **核心功能**:
  - 最近前沿策略自主探索
  - 状态机驱动的目标分配
  - 基于足迹的避障
  - 紧急停止服务调用
  - 适用于森林、废墟等非结构化环境
- **适用场景**: 危险环境自主探索巡检

### 3. unitree_go2_nav (Go2导航基础包)
- **链接**: https://github.com/Sayantani-Bhattacharya/unitree_go2_nav
- **Stars**: 88
- **支持机器人**: Go2
- **技术栈**: ROS 2 Jazzy, RTAB-Map, Nav2
- **核心功能**:
  - 建图模式 (mapping.launch.py)
  - 导航模式 (navigation.launch.py)
  - 2D目标位姿导航
  - 可作为子模块集成到其他项目
- **适用场景**: 作为基础导航包二次开发

### 4. Go2Controller / go2_ros2_sdk (NESL/UCLA)
- **链接**: https://github.com/nesl/Go2Controller (原 go2_ros2_sdk)
- **Stars**: 活跃社区
- **支持机器人**: Go2 AIR/PRO/EDU
- **技术栈**: ROS 2, WebRTC, CycloneDDS, slam_toolbox, Nav2, YOLO
- **核心功能**:
  - WebRTC (WiFi) 和 CycloneDDS (以太网) 双模式
  - 实时关节/IMU/足力传感器同步
  - LiDAR 点云流 + 相机流
  - SLAM (slam_toolbox)
  - Nav2 导航
  - COCO 物体检测
  - AutoPilot 自动驾驶
  - 支持多机器人
- **适用场景**: WiFi远程巡检，物体检测

### 5. go2_nav2_ros2 (Gazebo仿真导航)
- **链接**: https://github.com/arjun-sadananda/go2_nav2_ros2
- **支持机器人**: Go2
- **技术栈**: ROS 2 Humble, Gazebo, Nav2, CHAMP
- **核心功能**:
  - Gazebo 仿真环境（Amazon小型仓库）
  - 2D LiDAR 避障
  - Nav2 目标导航
- **适用场景**: 仿真验证，仓库巡检场景

---

## 三、避障 (Obstacle Avoidance)

### 1. unitree_nav (Go1 + Nav2)
- **链接**: https://github.com/ngmor/unitree_nav
- **Stars**: 活跃
- **支持机器人**: Go1
- **技术栈**: ROS 2 Humble, RoboSense RS-Helios-16P, RTAB-Map, Nav2
- **核心功能**:
  - Go1 高层模式控制
  - 3D LiDAR 建图
  - Nav2 自主导航避障
  - 服务化控制接口（damping, 设置姿态等）
- **适用场景**: Go1 平台的导航避障

### 2. Go1-Nav2-SDK
- **链接**: https://github.com/ShaunAlt-Unitree-Go1/Go1-Nav2-SDK
- **支持机器人**: Go1
- **技术栈**: ROS 2 Humble, SLAM, Nav2
- **核心功能**: Go1 SLAM + Navigation Stack
- **适用场景**: Go1 平台导航

### 3. Aliengo_2D_Nav-sim
- **链接**: https://github.com/guru-narayana/Aliengo_2D_Nav-sim
- **Stars**: 20
- **支持机器人**: AlienGo
- **技术栈**: ROS, Gazebo, RTAB-Map, Navigation Stack, m-explore
- **核心功能**:
  - 3D SLAM (RTAB-Map)
  - 2D 导航避障
  - 足步规划 (Foothold Planning)
  - 多模态步态控制
  - 深度相机 → 2D激光转换
- **适用场景**: 学术研究，室内巡检

### 4. AMIGO - 工业巡检系统 (Embry-Riddle航空大学)
- **链接**: https://github.com/eppl-erau-db/amigo_ros2
- **全称**: Autonomous Machine for Inspecting Gas and Operations
- **支持机器人**: Go2
- **技术栈**: ROS 2 Humble, NVIDIA Isaac ROS, Nav2, nvblox, RealSense D435i/D455, RPLiDAR A3, Jetson AGX Orin
- **核心功能**:
  - 工业环境自主巡检（气体检测、设备巡检）
  - 2D 地图建图 + 位姿记录
  - Nav2 自主导航
  - NVIDIA nvblox 3D导航（开发中）
  - Isaac ROS visual_slam
  - Docker 容器化部署
- **许可证**: MIT
- **适用场景**: **最接近实际工业巡检的项目**

---

## 四、爬楼梯 (Stair Climbing)

### 1. be2r_mpc-climbing_unitree ⭐专门爬楼梯
- **链接**: https://github.com/be2rlab/be2r_mpc-climbing_unitree
- **Stars**: 9
- **作者**: BE2R Lab (俄罗斯)
- **支持机器人**: A1
- **技术栈**: C++, Raisim仿真, 凸MPC, WBIC, RGB-D
- **核心功能**:
  - **专门针对楼梯攀爬**
  - 凸模型预测控制 (Convex MPC)
  - 全身脉冲控制器 (WBIC)
  - 基于 RGB-D 数据的楼梯感知
  - 有限状态机 (FSM) 控制
  - 支持多种求解器（qpOASES等）
- **论文**: "Design and performance evaluation of receding horizon controllers for quadrupedal robots: case study on stairs climbing and balancing"
- **适用场景**: **唯一的专门爬楼梯开源方案**

### 2. Nav2 爬楼梯讨论 (社区方案)
- **链接**: https://github.com/ros-navigation/navigation2/issues/5787
- **核心思路**:
  - 利用厂商自带的爬楼梯行为（如Go2自带的楼梯模式）
  - 2.5D 高程图替代 2D costmap
  - 自定义 3D 全局规划器
  - 实时在线 SLAM 构建多层地图
  - 将楼梯标记为高代价可通行区域而非致命障碍
- **适用场景**: 设计思路参考

---

## 五、导盲犬/辅助机器人 (特殊巡检应用)

### 1. Guide_dog_Unitree_Go1 (导盲犬项目)
- **链接**: https://github.com/Marnonel6/Guide_dog_Unitree_Go1
- **Stars**: 46
- **支持机器人**: Go1
- **技术栈**: ROS 2, 语音识别, YOLOv7物体检测, 自主导航, LiDAR
- **核心功能**:
  - 语音控制机器狗移动
  - 实时物体检测与避障
  - 自主导航辅助视障人士
  - 多传感器融合
- **适用场景**: 辅助巡检（语音控制 + 物体检测）

---

## 六、Python接口/仿真

### 1. Go2Py
- **链接**: https://github.com/machines-in-motion/Go2Py
- **Stars**: 活跃
- **支持机器人**: Go2
- **技术栈**: Python, C++, ROS2, MuJoCo, Pinocchio, Docker
- **核心功能**:
  - Python 化的底层/高层控制接口
  - Docker 化 ROS2 桥接
  - 紧急停止安全系统
  - MuJoCo 仿真环境
  - Pinocchio 运动学/动力学计算
  - FSM 状态机管理
- **适用场景**: 快速原型开发，Python 用户友好

---

## 项目对比总览

| 项目 | 机器人 | 建图 | 导航 | 避障 | 爬楼 | 真机 | 仿真 | 推荐度 |
|---|---|---|---|---|---|---|---|---|
| autonomy_stack_go2 | Go2 | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| OM1 ROS2 SDK | Go2/G1 | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ⭐⭐⭐⭐ |
| go2AutonomousNavigation | Go2 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⭐⭐⭐⭐ |
| AMIGO | Go2 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⭐⭐⭐⭐ |
| Go2Controller | Go2 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⭐⭐⭐⭐ |
| be2r_mpc-climbing | A1 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ |
| unitree_go2_nav | Go2 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⭐⭐⭐ |
| exploration_go2 | Go2 | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ⭐⭐⭐ |
| unitree_nav | Go1 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⭐⭐⭐ |
| Guide_dog_Go1 | Go1 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⭐⭐⭐ |
| Aliengo_2D_Nav | AlienGo | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ⭐⭐ |
| go2-slam-nav2 | Go2 | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ⭐⭐ |
| Go2Py | Go2 | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ⭐⭐ |

---

## 快速选型建议

1. **想做完整的Go2巡检系统（不改硬件）** → `autonomy_stack_go2` (CMU)
2. **需要工业级巡检能力** → `AMIGO` (Embry-Riddle)
3. **需要WiFi远程控制+SLAM** → `Go2Controller` (NESL)
4. **需要多机器人+自动充电** → `OM1 ROS2 SDK`
5. **专门研究爬楼梯算法** → `be2r_mpc-climbing_unitree`
6. **Python快速原型** → `Go2Py`
7. **Go1平台巡检** → `unitree_nav`
