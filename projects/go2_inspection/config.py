# Go2 巡检仿真系统 - 配置文件

import os

UNITREE_WS = os.path.expanduser("~/unitree_ws")

# ============================================
# 仿真配置
# ============================================
_model_rel = "git/official/unitree_mujoco/unitree_robots/go2/go2.xml"
_model_path = os.path.join(os.path.dirname(__file__), "../../../", _model_rel)
if not os.path.exists(_model_path):
    _model_path = os.path.join(UNITREE_WS, _model_rel)

SIMULATION = {
    "fps": 500,                          # 物理仿真频率 (Hz)
    "web_fps": 20,                       # Web数据推送频率 (Hz)
    "model_path": _model_path,
}

# ============================================
# LiDAR 配置 (模拟 L1 LiDAR)
# ============================================
LIDAR = {
    "horizontal_fov": 140,               # 水平视场角 (±70°)
    "horizontal_resolution": 0.5,        # 水平分辨率 (度)
    "max_range": 10.0,                   # 最大探测距离 (米)
    "min_range": 0.1,                    # 最小探测距离 (米)
    "frequency": 10,                     # 扫描频率 (Hz)
}

# ============================================
# 地图配置
# ============================================
MAPPING = {
    "resolution": 0.05,                  # 栅格分辨率 (米)
    "width": 200,                        # 栅格宽度 (格)
    "height": 200,                       # 栅格高度 (格)
    "origin_x": -5.0,                    # 地图原点X (米)
    "origin_y": -5.0,                    # 地图原点Y (米)
    "occupied_threshold": 0.65,          # 占据概率阈值
    "free_threshold": 0.35,              # 空闲概率阈值
}

# ============================================
# 地图存储配置
# ============================================
STORAGE = {
    "map_dir": os.path.join(os.path.dirname(__file__), "storage/maps"),
    "export_dir": os.path.join(os.path.dirname(__file__), "storage/exports"),
}

# ============================================
# Web服务配置
# ============================================
WEB = {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": False,
}

# ============================================
# 机器人控制参数
# ============================================
ROBOT = {
    "max_velocity_x": 1.0,               # 最大前后速度 (m/s)
    "max_velocity_y": 0.6,               # 最大左右速度 (m/s)
    "max_yaw_rate": 1.0,                 # 最大旋转速度 (rad/s)
    "control_force_xy": 500.0,           # XY方向控制力
    "control_force_z": 200.0,            # Z方向控制力
    "control_torque": 50.0,              # 旋转控制力矩
    "stand_height": 0.35,                # 站立高度 (米)
    "down_height": 0.15,                 # 趴下高度 (米)
}

# ============================================
# 巡检配置 (Phase 2)
# ============================================
INSPECTION = {
    "waypoint_tolerance": 0.2,           # 到达航点容差 (米)
    "scan_duration": 2.0,                # 每个点扫描时间 (秒)
    "path_planning_algorithm": "astar",  # 路径规划算法
}
