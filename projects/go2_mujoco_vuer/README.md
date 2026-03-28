# MuJoCo Go2/G1 Web Simulation

基于 MuJoCo 的 Unitree Go2/G1 机器人仿真，提供 Web 界面实时可视化。

## 功能特性

- ✅ 支持 Go2 和 G1 机器人模型切换
- ✅ 500Hz 物理仿真，30Hz 界面更新
- ✅ WebSocket 实时状态推送
- ✅ Three.js 3D 可视化
- ✅ REST API 控制接口
- ✅ 可选 DDS 桥接（连接 Unitree SDK）

## 项目结构

```
go2_mujoco_vuer/
├── config.py           # 机器人和仿真配置
├── sim/
│   ├── simulator.py    # MuJoCo 仿真管理
│   └── bridge.py       # DDS 桥接（可选）
├── web/
│   ├── app.py          # FastAPI Web 服务器
│   └── templates/
│       └── index.html  # 前端界面
├── requirements.txt
├── environment.yml
└── README.md
```

## 快速开始

### 1. 创建 Conda 环境

```bash
conda env create -f environment.yml
conda activate mujoco-sim
```

### 2. 启动仿真

```bash
cd projects/go2_mujoco_vuer
python web/app.py
```

### 3. 访问界面

浏览器打开：http://localhost:8080

## 界面说明

```
┌─────────────────────────────────────────────────────────┐
│  左侧面板                    │     3D 视图               │
│  ┌─────────────────────┐    │     ┌─────────────────┐   │
│  │ 机器人选择 (Go2/G1)  │    │     │                 │   │
│  │ [启动] [停止]        │    │     │   Three.js      │   │
│  │ [重置] [站立]        │    │     │   3D 渲染        │   │
│  │                     │    │     │                 │   │
│  │ 连接状态            │    │     │                 │   │
│  │ 机器人状态          │    │     └─────────────────┘   │
│  │ 关节角度            │    │                           │
│  └─────────────────────┘    │                           │
└─────────────────────────────────────────────────────────┘
```

## API 接口

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/robots` | 获取可用机器人列表 |
| POST | `/api/simulation/start/{robot}` | 启动仿真 |
| POST | `/api/simulation/stop` | 停止仿真 |
| POST | `/api/simulation/reset` | 重置仿真 |
| GET | `/api/simulation/state` | 获取当前状态 |
| POST | `/api/control` | 发送控制命令 |

### WebSocket

连接：`ws://localhost:8080/ws`

消息格式：
```json
{
  "type": "state",           // 状态更新
  "type": "control",         // 控制命令
  "type": "reset",           // 重置
  "type": "switch_robot"     // 切换机器人
}
```

## 使用 DDS 桥接（可选）

如果需要连接 Unitree SDK：

1. 安装 SDK：
```bash
cd ../../git/official/unitree_sdk2_python
pip install -e .
```

2. 启用桥接：
```python
from sim.bridge import create_bridge
from config import GO2_CONFIG, SIM_CONFIG

bridge = create_bridge(GO2_CONFIG, SIM_CONFIG)
if bridge:
    bridge.start()
```

## 注意事项

1. **首次运行**：MuJoCo 模型加载可能需要几秒钟
2. **模型切换**：切换机器人会重启仿真
3. **性能**：500Hz 仿真需要较好的 CPU
4. **浏览器**：推荐使用 Chrome/Edge

## 故障排除

### MuJoCo 导入错误
```bash
pip install mujoco --upgrade
```

### 端口被占用
修改 `config.py` 中的 `web_port`:
```python
SIM_CONFIG = SimConfig(web_port=8081)
```

### 模型加载失败
检查模型路径：
```bash
ls ../../git/official/unitree_mujoco/unitree_robots/go2/
ls ../../git/official/unitree_mujoco/unitree_robots/g1/
```

## 后续计划

- [ ] 集成 Vuer 做更高质量的 3D 渲染
- [ ] 支持更多机器人模型 (H1, B2)
- [ ] 添加轨迹可视化
- [ ] 添加 LiDAR 点云显示
- [ ] 支持键盘/手柄控制
