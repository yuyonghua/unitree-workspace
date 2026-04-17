# go2_motion_G
Go2 高级运动控制模块 (Sim & Real)

本项目是一个类似于官方 `SportClient` 的高级运动控制封装，底层通过强化学习 (RL) 策略直接计算 12 个关节的力矩，对外提供简单直观的接口。
通过解耦的 DDS 通信层，实现了一套代码同时支持 **MuJoCo 仿真跑测** 和 **真实 Go2 硬件部署**。

## 目录结构
- `configs/`
  - `go2_sim.yaml`: 仿真通信、控制与策略配置文件
  - `go2_real.yaml`: 真机硬件配置文件
- `go2_motion/`
  - `motion_client.py`: 提供给开发者使用的高级核心接口 `MotionClient`
  - `comm/`
    - `dds_comm.py`: CycloneDDS 核心通讯逻辑，自动打包/解析 IDL 数据并对数据流做 CRC 校验
    - `remote_controller.py`: SDK 字节流真机遥控器解析工具
    - `robot_state.py`: 解耦后的通用机器人状态抽象类
  - `control/`
    - `safety.py`: 控制限位和安全力矩裁剪
    - `joint_mapping.py`: 透明处理 RL 模型按序的 FL/FR/RL/RR 与 SDK 底层 FR/FL/RR/RL 不一致的设计
  - `policy/`
    - `obs_builder.py`: 将当前 RobotState 构建为 45 维度的 RL 模型 Observation (兼容各类四族 MoE 或 CTS 模型)
    - `rl_policy.py`: 调用 PyTorch 的基于 `.pt` 文件的 TorchScript 动作网络
    - `stand_policy.py`: 基础零动作 fallback 策略
- `models/`
  - 存放 `go2_policy.pt` 等预训练 RL 模型文件
- `scripts/`
  - `test_basic_control.py`: Phase 1 基础通讯与 PD 站立测试
  - `run_sim.py`: 仿真环境下集成测试脚本，走正方形路径
  - `run_real.py`: 真机部署安全工作流入口，带遥控器保护支持

## 运行仿真验证
1. 打开终端，启动 MuJoCo：
```bash
conda activate go2-sim
cd ~/unitree-workspace/git/official/unitree_mujoco/simulate_python
# 请确保 config.py 中 USE_JOYSTICK = 0
python unitree_mujoco.py
```

2. 另开终端，执行全功能测试路线：
```bash
conda activate go2-sim
cd ~/unitree-workspace/projects/go2_motion_G
export PYTHONPATH=.
python scripts/run_sim.py
```

## 运行真机验证
> ⚠️ **安全警告**: 首次部署请务必将 Go2 悬空支起！禁用 App Sport Mode 并在安全区域操作！

1. 在 Jetson Orin 等随车计算设备中：
```bash
cd ~/unitree-workspace/projects/go2_motion_G
export PYTHONPATH=.
# 根据自身配置环境指定网卡，通常为 eth0
python scripts/run_real.py --interface eth0
```

2. 操作流程：
- 启动后进入**瘫软 (DAMP)**
- 手柄按下 `Start`，进入**站起 (STAND)**
- 手柄按下 `A`，进入 **强化控制行走 (RL)** ，此时使用摇杆操控前后左右
- 突发意外直接按 `Select`，强制断电瘫软。
