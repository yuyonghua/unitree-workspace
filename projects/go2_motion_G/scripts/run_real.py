import time
import os
import argparse
import sys

from go2_motion.config import Go2Config
from go2_motion.motion_client import MotionClient, MotionState
from go2_motion.comm.remote_controller import RemoteController

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Run Go2 RL Policy on Real Robot.")
    parser.add_argument("--interface", type=str, default="eth0", help="Network interface (e.g., eth0, enp3s0)")
    args = parser.parse_args()

    config_path = os.path.join(get_project_root(), "configs/go2_real.yaml")
    print(f"Loading real config from {config_path}")
    
    config = Go2Config.from_yaml(config_path)
    
    # 覆盖 interface
    config.interface = args.interface
    print(f"Loaded config: {config}")

    client = MotionClient(config)
    rc_parser = RemoteController()
    
    print("\n--- SAFETY WARNING ---")
    print("1. Ensure robot is HUNG UP in the air for the first test.")
    print("2. Ensure sport mode is disabled via the App.")
    print("3. When ready, press START on joystick to move to default stand position.")
    print("4. Press A to enable RL walking mode.")
    print("5. Press SELECT (or Ctrl+C) to enter damping mode and exit.")
    print("----------------------\n")

    print(f"Initializing connection on {config.interface} [domain_id={config.domain_id}] ...")
    try:
        client.Init()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)
        
    print("Starting control loop in DAMPING mode...")
    client.Start()
    client.Damp()  # Safety first
    
    state_machine = "DAMP"  # DAMP -> STAND -> RL
    
    try:
        while True:
            # 1. 阅读遥控器
            state = client.comm.get_state()
            if not state.is_valid():
                time.sleep(0.01)
                continue
                
            rc = rc_parser.parse(state.wireless_remote)
            
            # 2. 状态机迁移
            if rc.btn_select:
                print("Emergency Stop requested via RC (SELECT pressed)!")
                break
                
            if state_machine == "DAMP" and rc.btn_start:
                print("Transitioning to Default Stand Position...")
                client.StandUp()
                state_machine = "STAND"
                time.sleep(0.5) # debounce
                
            elif state_machine == "STAND" and rc.btn_A:
                print("Enabling RL Walking Control...")
                state_machine = "RL"
                time.sleep(0.5) # debounce
                
            # 3. 如果在 RL 模式，允许摇杆输入
            if state_machine == "RL":
                # lx: 左右平移 (vy), ly: 前后 (vx), rx: 转向 (vyaw)
                # 这取决于真实摇杆的绑定
                # 常规绑定: 以左摇杆为主摇杆 (前进/平移), 右摇杆为副摇杆 (转向)
                vx = rc.ly * config.max_cmd[0]
                vy = -rc.lx * config.max_cmd[1]  # 注意方向
                vyaw = -rc.rx * config.max_cmd[2]
                
                # 平滑去死区
                if abs(vx) < 0.1: vx = 0.0
                if abs(vy) < 0.1: vy = 0.0
                if abs(vyaw) < 0.1: vyaw = 0.0
                
                if vx == 0 and vy == 0 and vyaw == 0:
                    client.StandUp()
                else:
                    client.Move(vx, vy, vyaw)
                    
            time.sleep(0.02)
            
    except KeyboardInterrupt:
        print("\nInterrupted by user (Ctrl+C).")
    finally:
        print("Stopping client and entering damping mode...")
        client.Stop()

if __name__ == "__main__":
    main()
