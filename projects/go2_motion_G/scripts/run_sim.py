import time
import os
import argparse
import sys
import select
import termios
import tty
import numpy as np

from go2_motion.config import Go2Config
from go2_motion.motion_client import MotionClient, MotionState

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class KeyboardController:
    """非阻塞键盘读取器"""
    def __init__(self):
        self.settings = termios.tcgetattr(sys.stdin)
        
    def get_key(self, timeout=0.1):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            key = sys.stdin.read(1)
        else:
            key = ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

def main():
    parser = argparse.ArgumentParser(description="Run Go2 RL Policy with Keyboard Control.")
    parser.add_argument("--config", type=str, default="configs/go2_sim.yaml")
    args = parser.parse_args()

    config_path = os.path.join(get_project_root(), args.config)
    config = Go2Config.from_yaml(config_path)
    client = MotionClient(config)
    
    # 速度上下界
    max_vx, max_vy, max_vyaw = config.max_cmd
    
    # 当前指令状态
    cmd_vx = 0.0
    cmd_vy = 0.0
    cmd_vyaw = 0.0

    print("Initializing client...")
    client.Init()
    client.Start()
    
    print("\n=== Keyboard Teleop Mode ===")
    print("W/S : Forward/Backward (Left Stick Y)")
    print("A/D : Left/Right       (Left Stick X)")
    print("J/L : Turn Left/Right  (Right Stick X)")
    print("Space : STOP moving")
    print("Enter : Toggle STAND/WALK mode")
    print("Q/ESC : Quit and DAMP")
    print("============================")
    
    client.StandUp()
    
    kbd = KeyboardController()
    mode = "STAND"
    
    try:
        while True:
            key = kbd.get_key(0.05)
            
            if key == '\x1b' or key.lower() == 'q':  # ESC 或 Q 退出
                break
            elif key == '\r':  # Enter 切换模式
                if mode == "STAND":
                    mode = "WALK"
                    client.Move(0, 0, 0)
                else:
                    mode = "STAND"
                    cmd_vx = cmd_vy = cmd_vyaw = 0.0
                    client.StandUp()
                print(f"\rSwitching to Mode: {mode}{' '*20}")
            
            if mode == "WALK":
                if key.lower() == 'w':
                    cmd_vx = min(max_vx, cmd_vx + 0.1)
                elif key.lower() == 's':
                    cmd_vx = max(-max_vx, cmd_vx - 0.1)
                elif key.lower() == 'a':
                    cmd_vy = min(max_vy, cmd_vy + 0.1)
                elif key.lower() == 'd':
                    cmd_vy = max(-max_vy, cmd_vy - 0.1)
                elif key.lower() == 'j':
                    cmd_vyaw = min(max_vyaw, cmd_vyaw + 0.1)
                elif key.lower() == 'l':
                    cmd_vyaw = max(-max_vyaw, cmd_vyaw - 0.1)
                elif key == ' ':
                    cmd_vx = cmd_vy = cmd_vyaw = 0.0
                else:
                    # 自动轻微衰减 (模拟摇杆回弹)
                    cmd_vx *= 0.95
                    cmd_vy *= 0.95
                    cmd_vyaw *= 0.95
                    
                # 消除接近0的误差
                if abs(cmd_vx) < 0.05: cmd_vx = 0.0
                if abs(cmd_vy) < 0.05: cmd_vy = 0.0
                if abs(cmd_vyaw) < 0.05: cmd_vyaw = 0.0

                client.Move(cmd_vx, cmd_vy, cmd_vyaw)
                
                # 在同一行刷新状态，避免疯狂刷屏
                sys.stdout.write(f"\r[WALK] vx: {cmd_vx:5.2f} | vy: {cmd_vy:5.2f} | vyaw: {cmd_vyaw:5.2f}{' '*10}")
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("\nStopping client...")
        client.Stop()

if __name__ == "__main__":
    main()
