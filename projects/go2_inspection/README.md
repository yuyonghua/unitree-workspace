# Go2 巡检仿真系统

基于MuJoCo仿真的Unitree Go2机器狗Web巡检系统，支持建图、地图保存和巡检任务。

## 功能特性

- **MuJoCo物理仿真** - 500Hz仿真频率，Headless模式运行
- **Web控制界面** - 浏览器远程操作，键盘/摇杆控制
- **LiDAR模拟** - 模拟L1雷达扫描，生成点云数据
- **建图功能** - 实时生成占据栅格地图，支持保存/加载
- **巡检任务** - 航点巡检，自动扫描（Phase 2）

## 快速开始

### 环境要求

- Conda (Miniconda 或 Anaconda)
- Python 3.10

### 创建环境（首次）

```bash
conda create -n go2-inspection python=3.10 -y
conda activate go2-inspection
cd projects/go2_inspection
pip install -r requirements.txt
```

### 启动系统

```bash
conda activate go2-inspection
./start.sh
# 或直接运行
python web/app.py
```

访问 http://localhost:8000

## 使用说明

### 控制方式

| 按键 | 功能 |
|------|------|
| W/S | 前进/后退 |
| A/D | 左移/右移 |
| ←/→ | 左转/右转 |
| 空格 | 停止 |

### 建图流程

1. 点击"启动仿真"
2. 点击"站起"
3. 点击"开始建图"
4. 使用WASD控制机器人扫描区域
5. 点击"停止建图"
6. 输入地图名称，点击"保存地图"

### 加载地图

在左侧地图列表中点击已保存的地图名称即可加载。

## 项目结构

```
go2_inspection/
├── config.py              # 配置常量
├── requirements.txt       # Python依赖
├── start.sh               # 启动脚本
├── sim/                   # 仿真模块
│   ├── simulator.py       # MuJoCo仿真器
│   └── lidar.py           # LiDAR模拟
├── mapping/               # 建图模块
│   ├── mapper.py          # 地图构建器
│   └── occupancy_grid.py  # 占据栅格算法
├── storage/               # 地图存储
│   ├── manager.py         # 地图文件管理
│   └── maps/              # 地图文件目录
├── web/                   # Web服务
│   ├── app.py             # FastAPI主程序
│   └── templates/
│       └── index.html     # 前端界面
└── control/               # 控制算法（Phase 2）
    ├── navigation.py      # 路径规划
    └── inspection.py      # 巡检逻辑
```

## API接口

### 仿真控制

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/connect` | POST | 启动仿真 |
| `/api/disconnect` | POST | 停止仿真 |
| `/api/stand_up` | POST | 站起 |
| `/api/stand_down` | POST | 趴下 |
| `/api/stop` | POST | 停止移动 |
| `/api/move` | POST | 发送速度命令 |
| `/api/status` | GET | 获取状态 |

### 地图管理

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/map/start_mapping` | POST | 开始建图 |
| `/api/map/stop_mapping` | POST | 停止建图 |
| `/api/map/save` | POST | 保存地图 |
| `/api/map/list` | GET | 地图列表 |
| `/api/map/load/{name}` | POST | 加载地图 |
| `/api/map/delete/{name}` | DELETE | 删除地图 |

## 参考文档

- MuJoCo官方文档: https://mujoco.readthedocs.io/
- FastAPI文档: https://fastapi.tiangolo.com/
- Go2 SDK文档: `docs/Unitree_Go2_SDK_文档全集.md`
