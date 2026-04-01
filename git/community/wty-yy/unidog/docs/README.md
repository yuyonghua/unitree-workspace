# UniDog - 机器狗智能巡检与语音控制系统

## 项目概述

基于 Unitree Go2-edu 四足机器狗，结合强化学习运控、激光雷达建图、导航避障和大语言模型语音控制的完整智能机器人系统。

**技术来源**：首届腾讯开悟具身智能强化学习运控挑战赛冠军方案  
**核心框架**：wty-yy/go2_rl_gym + RoboGauge + unitree_cpp_deploy  
**相关论文**：Toward Reliable Sim-to-Real Predictability for MoE-based Robust Quadrupedal Locomotion (ArXiv:2602.00678)

---

## 核心能力

| 模块 | 能力描述 |
|------|---------|
| **运控层** | 基于 MoE 强化学习网络的 500Hz 底层力矩控制，纯本体感知无需视觉 |
| **建图层** | 基于 Livox LIS-3D/Mid-360 激光雷达的 Point-LIO 实时建图 |
| **导航层** | ROS2 Nav2 全局路径规划 + DWA 局部避障 |
| **交互层** | MCP + LLM 实现自然语言语音控制 |
| **可视化** | Web 端实时点云/地图渲染 + 遥控界面 |

---

## 关键技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 运控 | unitree_cpp_deploy (C++) | ONNX 推理，500Hz 实时控制 |
| 建图 | Point-LIO + OccupancyGrid | 激光雷达 SLAM |
| 导航 | ROS2 Humble + Nav2 | 路径规划与避障 |
| 通信 | CycloneDDS | ROS2 底层通信 |
| Web 后端 | Python asyncio + WebSocket | 实时数据转发 |
| Web 前端 | Vue 3 + Three.js + Canvas | 2D/3D 可视化 |
| 语音 | Whisper STT + Claude/GPT-4o | 自然语言理解 |
| 控制协议 | MCP (Model Context Protocol) | LLM 工具调用 |

---

## 开发环境

- **操作系统**：Windows 11 + WSL2 Ubuntu 22.04
- **IDE**：VSCode + Remote-WSL 插件
- **浏览器**：Chrome / Edge（Web 可视化）
- **仿真**：unitree_mujoco (C++ MuJoCo 仿真器)

---

## 项目结构

```
unidog/
├── docs/                          # 文档
│   ├── README.md                  # 本文件
│   ├── architecture/              # 架构文档
│   │   ├── system_overview.md     # 系统总体架构
│   │   ├── layer_design.md       # 分层设计
│   │   ├── data_flow.md          # 数据流设计
│   │   └── module_spec.md        # 模块规格说明
│   ├── development/               # 开发指南
│   │   ├── setup_env.md          # 环境搭建
│   │   ├── phases/               # 阶段开发指南
│   │   │   ├── phase1_env.md     # 阶段一：环境搭建
│   │   │   ├── phase2_visual.md   # 阶段二：Web 可视化
│   │   │   ├── phase3_mapping.md  # 阶段三：遥控+建图
│   │   │   ├── phase4_nav.md     # 阶段四：导航避障
│   │   │   └── phase5_voice.md   # 阶段五：语音控制
│   │   └── deployment.md         # 真机部署指南
│   └── reference/                # 参考资料
│       ├── hardware.md          # 硬件规格
│       ├── lidar_specs.md      # 雷达规格对比
│       └── troubleshooting.md   # 常见问题
├── scripts/                      # 脚本工具
│   └── setup_env.sh             # 环境一键安装脚本
└── workspace/                    # 开发工作区 (git/ 下各项目)
    ├── unitree_sdk2/            # 宇树官方 SDK
    ├── unitree_mujoco/          # C++ 仿真器
    ├── wty-yy/                  # wty-yy 强化学习方案
    │   ├── go2_rl_gym/         # 训练框架
    │   ├── RoboGauge/           # 评估框架
    │   └── unitree_cpp_deploy/  # C++ 部署
    ├── ros2_ws/                 # ROS2 工作空间
    └── unidog_ws/               # 自己的 Web 服务工作区
```

---

## 快速开始

### 阶段一：环境验证（现在就可以做）

```bash
# 1. 检查 WSLg
ls /mnt/wslg

# 2. 检查 NVIDIA
nvidia-smi

# 3. 编译仿真器
cd ~/git/official/unitree_mujoco/simulate
mkdir build && cd build
cmake .. && make -j$(nproc)
./unitree_mujoco

# 4. 测试 ROS2
source /opt/ros/humble/setup.bash
ros2 run rviz2 rviz2 &
```

### 完整开发路线图

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| 阶段一 | 环境搭建 + 仿真器验证 | 1-2 周 |
| 阶段二 | WebSocket Bridge + 可视化基础 | 2 周 |
| 阶段三 | 遥控 + 建图功能 | 2 周 |
| 阶段四 | 导航 + 避障 | 1-2 周 |
| 阶段五 | 语音 + MCP 控制 | 1 周 |
| 阶段六 | 真机部署 | 1 周 |

---

## 维护记录

| 日期 | 版本 | 修改内容 |
|------|------|---------|
| 2026-03-31 | v1.0 | 初始架构设计 |
