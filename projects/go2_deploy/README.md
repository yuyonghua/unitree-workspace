# go2_deploy

Go2 强化学习运动控制部署工具。单线程架构，100% 复刻 `go2_rl_gym` 的控制逻辑，支持仿真/真机双模部署。

## 文件结构

```
go2_deploy/
├── config.yaml      # 统一配置 (参数对齐 go2_rl_gym)
├── controller.py    # 核心控制器 (DDS + RL + 状态机)
├── run.py           # 入口脚本 (键盘/遥控器控制)
└── README.md
```

## 仿真运行

```bash
# 终端 1: 启动仿真器
conda activate go2-sim
cd ~/unitree-workspace/git/official/unitree_mujoco/simulate_python
python unitree_mujoco.py

# 终端 2: 启动控制器
conda activate go2-sim
cd ~/unitree-workspace/projects/go2_deploy
python run.py
```

## 真机运行

⚠️ **首次测试请将机器人悬空！必须在 App 中关闭 sport mode！**

```bash
python run.py --interface eth0 --domain 0
```

## 操作说明

| 按键 | 功能 |
|------|------|
| `1` | 站起 |
| `2` | 趴下 |
| `3` | 切换 RL 行走模式 |
| `W/S` | 前进 / 后退 |
| `A/D` | 左 / 右平移 |
| `J/L` | 左 / 右转 |
| `Space` | 急停 (速度归零) |
| `Q/ESC` | 安全退出 (自动趴下 → 阻尼) |

真机遥控器: `Start`=站起, `A`=RL行走, `Select`=退出, 摇杆控制移动。

## 安全机制

- 退出时**自动执行**: 减速 → 趴下 → 阻尼
- Ctrl+C 也会触发安全关机序列
- 站立使用高增益 PD (kp=40, kd=0.6) 确保稳定
- 行走使用 RL 训练匹配的 PD (kp=20, kd=0.5)
