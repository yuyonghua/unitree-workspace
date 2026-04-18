#!/usr/bin/env python3
"""
自动化冒烟测试: 站起 → RL行走3秒 → 趴下 → 阻尼退出
无需键盘交互, 用于验证控制链路是否正常。
"""
import time
import sys
from controller import Go2Controller, Config

def main():
    config = Config("config.yaml")
    print(f"Config OK: interface={config.interface}, domain_id={config.domain_id}")

    ctrl = Go2Controller(config)
    ctrl.init_dds()
    ctrl.wait_for_connection()

    try:
        # 1. 零力矩
        print("\n[1/5] Zero torque (0.5s)...")
        ctrl.send_zero_torque(duration=0.5)

        # 2. 站起
        print("[2/5] Standing up...")
        ctrl.stand_up()

        # 3. 维持站立 1s
        print("[3/5] Holding stand (1s)...")
        for _ in range(50):
            ctrl.hold_stand()
            time.sleep(config.control_dt)

        # 4. RL 行走 3s (前进 vx=0.5)
        print("[4/5] RL walking forward (3s, vx=0.5)...")
        ctrl.set_cmd(0.5, 0.0, 0.0)
        for i in range(150):
            ctrl.rl_step()
            time.sleep(config.control_dt)
            if i % 50 == 0:
                print(f"  ... step {i}/150")

        # 停下
        print("  Decelerating...")
        ctrl.set_cmd(0.0, 0.0, 0.0)
        for _ in range(25):
            ctrl.rl_step()
            time.sleep(config.control_dt)

        # 5. 趴下
        print("[5/5] Lying down...")
        ctrl.lie_down()

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        # 始终发送阻尼
        print("Sending damping...")
        for _ in range(10):
            ctrl.send_damping()
            time.sleep(config.control_dt)
        print("Test complete!")

if __name__ == "__main__":
    main()
