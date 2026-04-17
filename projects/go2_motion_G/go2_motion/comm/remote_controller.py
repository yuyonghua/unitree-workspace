import struct
from dataclasses import dataclass
from typing import Tuple

@dataclass
class RemoteControllerData:
    lx: float = 0.0          # Left stick X [-1.0, 1.0]
    ly: float = 0.0          # Left stick Y [-1.0, 1.0]
    rx: float = 0.0          # Right stick X [-1.0, 1.0]
    ry: float = 0.0          # Right stick Y [-1.0, 1.0]
    
    # Buttons
    btn_R1: bool = False
    btn_L1: bool = False
    btn_start: bool = False
    btn_select: bool = False
    btn_R2: bool = False
    btn_L2: bool = False
    btn_F1: bool = False
    btn_F2: bool = False
    btn_A: bool = False
    btn_B: bool = False
    btn_X: bool = False
    btn_Y: bool = False
    btn_up: bool = False
    btn_right: bool = False
    btn_down: bool = False
    btn_left: bool = False

class RemoteController:
    """
    解析 unitree_go_msg_dds__LowState_ 的 wireless_remote 字段
    """
    def __init__(self):
        self.data = RemoteControllerData()
        
    def parse(self, raw_bytes: bytes) -> RemoteControllerData:
        """
        从 40 字节原始数据中解析遥控器状态。
        数据结构 (unitree SDK):
        - head[2]
        - btn.components
        - lx, rx, ry, ly, paddle (float32)
        """
        if len(raw_bytes) < 40:
            return self.data
            
        try:
            # 遥控器的组成部分:
            # bytes[2:4] 是遥控器按键 16-bit 掩码
            btn_value = struct.unpack('<H', raw_bytes[2:4])[0]
            
            self.data.btn_R1     = bool(btn_value & (1 << 0))
            self.data.btn_L1     = bool(btn_value & (1 << 1))
            self.data.btn_start  = bool(btn_value & (1 << 2))
            self.data.btn_select = bool(btn_value & (1 << 3))
            self.data.btn_R2     = bool(btn_value & (1 << 4))
            self.data.btn_L2     = bool(btn_value & (1 << 5))
            self.data.btn_F1     = bool(btn_value & (1 << 6))
            self.data.btn_F2     = bool(btn_value & (1 << 7))
            self.data.btn_A      = bool(btn_value & (1 << 8))
            self.data.btn_B      = bool(btn_value & (1 << 9))
            self.data.btn_X      = bool(btn_value & (1 << 10))
            self.data.btn_Y      = bool(btn_value & (1 << 11))
            self.data.btn_up     = bool(btn_value & (1 << 12))
            self.data.btn_right  = bool(btn_value & (1 << 13))
            self.data.btn_down   = bool(btn_value & (1 << 14))
            self.data.btn_left   = bool(btn_value & (1 << 15))
            
            # 摇杆数据在偏移量 4 之后
            # lx, rx, ry, ly, ... (4个float32)
            lx, rx, ry, ly = struct.unpack('<ffff', raw_bytes[4:20])
            self.data.lx = lx
            self.data.rx = rx
            self.data.ry = ry
            self.data.ly = ly
            
        except Exception as e:
            print(f"[RemoteController] Failed to parse bytes: {e}")
            
        return self.data
