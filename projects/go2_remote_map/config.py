"""Go2 远程遥控与建图系统 - 配置文件"""

# ==================== 连接凭据 ====================

DEFAULT_REMOTE = {
    "serial_number": "B42N6000Q1496588",
    "username": "yyhstd@qq.com",
    "password": "Yuyh0102",
}

DEFAULT_LOCALSTA = {
    "ip": "10.114.97.227",
}

# ==================== 速度限制 ====================

SPEED_LIMITS = {
    "vx": 1.0,   # 前后 m/s (摇杆满量程映射)
    "vy": 0.6,   # 左右 m/s
    "vz": 1.0,   # 旋转 rad/s
}

# ==================== 雷达配置 ====================

LIDAR_CONFIG = {
    "decoder": "native",        # "native" 或 "libvoxel"
    "downsample_rate": 50,      # 每 N 个点取 1 个用于前端预览
    "max_preview_points": 2000, # 前端单帧最大点数上限
    "skip_frames": 1,           # 每 N 帧推送 1 帧到前端 (1=不跳帧)
}

# ==================== Web 服务配置 ====================

WEB_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
}

# ==================== 数据落盘配置 ====================

DATA_DIR = "data"
