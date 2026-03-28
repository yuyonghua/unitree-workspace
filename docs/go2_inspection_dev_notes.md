# Go2 巡检系统 - 开发记录与技术方案

> 本文档整理自 OpenCode 对话记录，包含项目背景、技术方案、踩坑记录等。

---

## 一、背景信息

### 你的身份与目标
- **角色**：机器人开发者，团队有多台 Unitree 机器人
- **机器人配置**：
  - Go2: Pro、X、EDU 各一台
  - G1: 人形机器人一台
- **终极目标**：开发 Go2 巡检系统，能控制机器狗扫描建立地图，然后在该区域执行巡检任务

### 开发环境
| 组件 | 配置 |
|------|------|
| **服务器** | 2× RTX 3090, 251GB RAM, 40核 CPU, Python 3.10, MuJoCo 3.6.0 |
| **访问方式** | SSH 连接，无 GUI |
| **客户端** | Windows 10（可切换 Ubuntu 22.04，但偏好 Windows） |

---

## 二、技术方案演进

### 2.1 仿真方案选择

**问题**：服务器无图形界面，如何高效仿真？

**解决方案**：服务器 headless 仿真 + Web UI

```
Windows 浏览器 → SSH隧道 → FastAPI后端 → MuJoCo headless仿真
                      ↓
               WebSocket (20Hz) → Three.js 3D可视化
```

### 2.2 开发环境选择

**问题**：conda 环境 vs 系统环境？

**决定**：使用 conda 环境隔离
```bash
conda create -n go2-inspection python=3.10 -y
```

### 2.3 3D 可视化方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Three.js** | 轻量、灵活、社区活跃 | 需自己搭建 | ⭐⭐⭐ |
| Babylon.js | 功能丰富 | 包体积大 | ⭐⭐ |
| Potree.js | 点云专用 | 不适合动态物体 | ⭐⭐ |
| PlayCanvas | 可视化编辑器 | 需账号 | ⭐ |

**决定**：Three.js（主场景）+ 可选 Potree.js（点云地图）

---

## 三、开发过程中的问题与解决

### 3.1 仿真器控制问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 狗不动 | 力太小 | `fx = vx * 800.0`（需足够大） |
| 站起/趴下无效 | `_standing` 状态未正确切换 | 修复状态管理 |
| 旋转方向反了 | yaw 符号错误 | 右转 = 负 yaw_rate |

### 3.2 LiDAR 问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 点云不显示 | 点数为 0 | 修复射线检测算法 |
| LiDAR 不跟随旋转 | 在 world frame 生成 | 改为 robot frame，前端转换 |
| L1 LiDAR 特性 | 应该是前置扇形 | ±70° FOV，非 360° |

### 3.3 前端控制问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 摇杆划不动 | 事件绑定失败 | 重新绑定 addEventListener |
| 摇杆松开不停 | 没发停止命令 | 20Hz setInterval 持续发命令 |
| 仿真界面全黑 | Three.js 初始化失败 | 确保 container 尺寸 > 0 |
| 键盘不响应 | 缺少事件处理 | 添加 keydown/keyup 监听 |

---

## 四、关键实现要点（踩坑记录）

### 4.1 MuJoCo 力控制
```python
# 太小不会动！
fx = self._vx * 800.0   # 至少 500+
tz = self._yaw_rate * 200.0
```

### 4.2 LiDAR 坐标转换
```python
# 后端：返回 robot frame 点云
points.append([local_x, local_y])

# 前端：转换到 world frame 显示
const wx = px * Math.cos(yaw) - py * Math.sin(yaw) + robotX;
const wz = px * Math.sin(yaw) + py * Math.cos(yaw) + robotY;
```

### 4.3 命令循环（必须！）
```javascript
// 摇杆/键盘需要持续发送命令，否则松开后机器人不会停
setInterval(() => {
    fetch('/api/move', { body: JSON.stringify({vx, vy, yaw}) });
}, 50);  // 20Hz
```

### 4.4 旋转方向约定
```python
# 右转 = 负 yaw（顺时针）
# 左转 = 正 yaw（逆时针）
yaw = -joystick.x * 0.8  # 右摇杆向右 → 负值
```

---

## 五、最终确定的项目需求

### 5.1 核心功能

| 模块 | 功能 |
|------|------|
| **F1. 仿真系统** | MuJoCo headless 500Hz, Go2 控制, L1 LiDAR 模拟 |
| **F2. Web 控制** | Three.js 3D可视化, 双摇杆, 键盘, 状态显示 |
| **F3. 建图系统** ⭐ | LiDAR数据采集, 地图生成, 保存/加载/管理 |
| **F4. 巡检功能** | 路径规划, 自动巡检 (Phase 2) |

### 5.2 最终工作流

```
Step 1: 建图模块
  启动仿真 → 控制狗扫描区域 → 生成地图 → 保存为JSON

Step 2: 巡检模块  
  导入地图 → 加载仿真 → 基于地图执行巡检任务

地图分享：
  导出JSON → 其他人导入 → 复用地图进行巡检
```

### 5.3 地图文件格式
```json
{
  "version": "1.0",
  "type": "occupancy_grid",
  "metadata": {"resolution": 0.05, "width": 200, "height": 200, ...},
  "data": [...]
}
```

---

## 六、环境配置

### Conda 环境
```bash
conda create -n go2-inspection python=3.10 -y
conda activate go2-inspection
```

### 工作空间结构

```
unitree_ws/
├── git/
│   ├── official/          # 官方SDK仓库（主要参考）
│   │   ├── unitree_sdk2/            # C++ SDK（核心）
│   │   ├── unitree_sdk2_python/     # Python SDK
│   │   ├── unitree_ros/             # 提供URDF机器人模型
│   │   ├── unitree_ros2/            # ROS2集成
│   │   ├── unitree_rl_gym/          # 强化学习训练（Isaac Gym）
│   │   ├── unitree_mujoco/          # Mujoco仿真
│   │   └── ...
│   └── community/         # 社区项目（仅作了解参考）
├── docs/                  # 文档
│   ├── ocs/go2_inspection_dev_notes.md # 需求文档
│   └── Unitree_Go2_SDK_文档全集.md  # 官方文档离线版
├── sample/                # 测试脚本（参考价值有限）
└── projects/              # 用户项目
```

### 启动命令
```bash
cd projects/go2_inspection
conda activate go2-inspection
./start.sh
# 访问: http://localhost:8000 (通过 SSH 隧道)
```

---

*文档版本: 1.0*
*创建日期: 2026-03-22*
