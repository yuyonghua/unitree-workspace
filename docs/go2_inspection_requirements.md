# Go2 Inspection System - 项目需求文档

## 📋 项目概述

开发一个基于 Web 的 Unitree Go2 机器狗巡检仿真系统，支持：
- MuJoCo 物理仿真（headless 模式）
- 3D 可视化界面（Three.js）
- 实时控制（键盘 + 双摇杆）
- L1 LiDAR 点云模拟
- WebSocket 实时数据传输

---

## 🎯 功能需求

### F1. 仿真核心
- [ ] MuJoCo headless 仿真，500Hz 物理步进
- [ ] Go2 机器人模型（使用 `git/official/unitree_mujoco/unitree_robots/go2/`）
- [ ] 支持站立/趴下姿态切换
- [ ] 支持前后移动、左右平移、旋转控制
- [ ] 简单步态模拟（trot 步态）

### F2. 3D 可视化
- [ ] Three.js 渲染引擎
- [ ] Go2 机器人模型（程序化生成，含身体、头部、四腿、尾巴）
- [ ] 地面网格 + 边界墙壁
- [ ] 障碍物显示（圆柱体）
- [ ] 运动轨迹线
- [ ] LiDAR 点云可视化（绿色点）

### F3. 控制系统
- [ ] **双摇杆控制**：
  - 左摇杆：前后/左右移动
  - 右摇杆：左转/右转
- [ ] **键盘控制**：
  - W/S：前进/后退
  - A/D：左移/右移
  - ←/→：左转/右转
  - 空格：紧急停止
- [ ] **按钮控制**：站起、趴下、停止
- [ ] 命令持续发送（20Hz），松开即停

### F4. LiDAR 模拟
- [ ] 模拟 L1 LiDAR（前置，±70° FOV）
- [ ] 检测墙壁和障碍物
- [ ] 点云随机器人朝向旋转
- [ ] 添加适量噪声增加真实感

### F5. Web 界面
- [ ] 左侧控制面板
- [ ] 右侧 3D 视图
- [ ] 状态显示（位置、速度、朝向）
- [ ] 实时日志面板

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows 客户机                            │
│  浏览器 http://localhost:8000 (通过 SSH 隧道)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Three.js 3D 视图  │  摇杆/键盘控制  │  状态显示      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                    WebSocket + REST API
                          │
┌─────────────────────────────────────────────────────────────┐
│                    服务器 (headless)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ FastAPI (port 8000)                                  │   │
│  │  - REST API: /api/connect, /api/stand_up, etc.      │   │
│  │  - WebSocket: /ws (20Hz 状态推送)                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Go2Simulator (MuJoCo headless)                       │   │
│  │  - 500Hz 物理步进                                     │   │
│  │  - PD 关节控制                                        │   │
│  │  - LiDAR 点云生成                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
projects/go2_inspection/
├── config.py           # 配置常量
├── requirements.txt    # Python 依赖
├── start.sh            # 启动脚本
├── sim/
│   ├── __init__.py
│   └── simulator.py    # MuJoCo 仿真器
├── control/
│   └── (预留：导航、避障算法)
└── web/
    ├── app.py          # FastAPI 后端
    └── templates/
        └── index.html  # 前端界面
```

---

## 🔧 环境配置

### Conda 环境
```bash
conda create -n go2-inspection python=3.10 -y
conda activate go2-inspection
```

### 依赖安装
```bash
pip install mujoco numpy fastapi uvicorn websockets jinja2 python-multipart
pip install /home/ubuntu/unitree_ws/git/official/unitree_sdk2_python --no-deps
```

### 启动命令
```bash
cd projects/go2_inspection
./start.sh  # 或: python web/app.py
```

---

## 📝 代码风格

### Python
```python
# 1. 标准库
import logging
import threading
from typing import Dict, List, Optional

# 2. 第三方
import numpy as np
import mujoco

# 3. 本地
from config import WEB_CONFIG

# 命名: snake_case 函数, PascalCase 类, UPPER_CASE 常量
class Go2Simulator:
    def stand_up(self) -> None:
        """站起姿态"""
        pass

# 错误处理: 返回字典
async def connect() -> Dict:
    try:
        return {"success": True, "message": "connected"}
    except Exception as e:
        logger.error(f"连接失败: {e}")
        return {"success": False, "message": str(e)}
```

### JavaScript (前端)
```javascript
// 使用 const/let，不用 var
// 异步使用 async/await
// DOM 操作用 getElementById
// 事件监听用 addEventListener
```

---

## ⚠️ 关键实现要点

### 1. LiDAR 坐标转换（重要）
LiDAR 点云必须在 **robot frame** 生成，前端显示时转换到 world frame：
```python
# 后端：返回 robot frame 点云
points.append([local_x, local_y])  # 相对于机器人朝向

# 前端：转换到 world frame 显示
const wx = px * Math.cos(yaw) - py * Math.sin(yaw) + robotX;
const wz = px * Math.sin(yaw) + py * Math.cos(yaw) + robotY;
```

### 2. 命令循环（重要）
必须使用定时器持续发送命令，否则摇杆松开后机器人不会停止：
```javascript
// 启动仿真后启动命令循环
setInterval(() => {
    sendCommand(vx, vy, yaw);
}, 50);  // 20Hz
```

### 3. 旋转方向（重要）
确保方向正确：
- 右箭头/右摇杆向右 = **负 yaw** (顺时针)
- 左箭头/左摇杆向左 = **正 yaw** (逆时针)

### 4. MuJoCo 力控制（重要）
需要足够大的力才能驱动机器人：
```python
fx = vx * 800.0   # 太小不会动
tz = yaw_rate * 200.0
```

---

## 🐛 已知问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 摇杆划不动 | 前端事件绑定失败 | 使用 addEventListener，检查元素 ID |
| 仿真界面全黑 | Three.js 初始化失败 | 确保 container 尺寸 > 0，检查 CDN 加载 |
| 摇杆松开不停 | 没有发送停止命令 | 使用 setInterval 持续发命令 |
| 狗不动 | 力太小 | 增大 fx 到 800+ |
| LiDAR 不转 | 坐标没转换 | 前端乘 cos(yaw)/sin(yaw) |
| 方向反了 | yaw 符号错 | 右转 = 负 yaw |

---

## 📚 参考资料

| 资源 | 路径/链接 |
|------|----------|
| MuJoCo Go2 模型 | `git/official/unitree_mujoco/unitree_robots/go2/` |
| MuJoCo Python API | https://mujoco.readthedocs.io/en/stable/python.html |
| Three.js 文档 | https://threejs.org/docs/ |
| FastAPI 文档 | https://fastapi.tiangolo.com/ |
| unitree_sdk2_python | `git/official/unitree_sdk2_python/` |

---

## ✅ 验证清单

完成开发后，按此清单验证：

### 基础功能
- [ ] 启动服务无报错
- [ ] 浏览器打开显示 3D 界面
- [ ] 点击"启动"后狗显示在场景中

### 控制测试
- [ ] W 键：狗向前移动
- [ ] S 键：狗向后移动
- [ ] A 键：狗向左平移
- [ ] D 键：狗向右平移
- [ ] ← 键：狗左转
- [ ] → 键：狗右转
- [ ] 空格键：狗停止
- [ ] 松开所有键：狗自动停止
- [ ] 左摇杆：控制移动
- [ ] 右摇杆：控制旋转

### 姿态测试
- [ ] 点击"站起"：狗站起来
- [ ] 点击"趴下"：狗趴下
- [ ] 站立状态才能移动

### LiDAR 测试
- [ ] 3D 视图显示绿色点云
- [ ] 点云在狗的前方扇形区域
- [ ] 旋转时点云跟随转动

### 状态显示
- [ ] X/Y 坐标实时更新
- [ ] 速度数值变化
- [ ] 朝向角度变化
- [ ] 仿真时间递增

---

## 🔄 迭代计划

### Phase 1: 基础仿真（当前）
- [x] MuJoCo 仿真器
- [ ] 3D 可视化
- [ ] 双摇杆 + 键盘控制
- [ ] LiDAR 显示

### Phase 2: 导航功能
- [ ] 路径规划
- [ ] 避障算法
- [ ] 地图构建

### Phase 3: 爬楼梯
- [ ] 地形检测
- [ ] 步态调整
- [ ] 坡度适应

### Phase 4: 多模型支持
- [ ] Go2 Pro/X/EDU 切换
- [ ] G1 人形机器人支持
