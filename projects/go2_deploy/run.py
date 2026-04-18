#!/usr/bin/env python3
"""
Go2 RL 部署主入口 — 键盘遥控版。

支持仿真 (unitree_mujoco) 和真机 (Go2 DDS) 双模式。
单线程运行, 无并发问题。

操作说明:
  1 - 站起
  2 - 趴下
  3 - 进入/退出 RL 行走模式
  W/S - 前进/后退
  A/D - 左/右平移
  J/L - 左/右转
  Space - 急停 (速度归零)
  Q/ESC - 安全退出 (趴下 → 阻尼)

真机额外支持遥控器:
  Start - 站起
  A     - 进入 RL 行走
  Select - 安全退出
"""

import os
import sys
import time
import select
import termios
import tty
import signal
import numpy as np
from pathlib import Path

from controller import Go2Controller, Config, KeyMap


# ============================================================
# 非阻塞键盘输入
# ============================================================

class KeyboardReader:
    """基于 termios 的非阻塞键盘读取"""

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)

    def get_key(self, timeout: float = 0.01) -> str:
        """非阻塞读取一个按键, 无按键返回空串"""
        try:
            tty.setraw(self.fd)
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if rlist:
                key = sys.stdin.read(1)
            else:
                key = ""
        finally:
            termios.tcsetattr(self.fd, termios.TCSANOW, self.old_settings)
        return key

    def restore(self):
        """恢复终端设置"""
        termios.tcsetattr(self.fd, termios.TCSANOW, self.old_settings)


# ============================================================
# 状态定义
# ============================================================

class State:
    IDLE = "IDLE"              # 等待连接
    ZERO_TORQUE = "ZERO"       # 零力矩 (初始瘫软)
    STANDING = "STAND"         # PD 站立保持
    RL_WALKING = "RL_WALK"     # RL 策略行走
    LYING_DOWN = "LIE_DOWN"    # 趴下中
    DAMPING = "DAMP"           # 阻尼终止


# ============================================================
# 主循环
# ============================================================

def main():
    # ---- 加载配置 ----
    config_path = str(Path(__file__).parent / "config.yaml")

    # 允许命令行覆盖
    import argparse
    parser = argparse.ArgumentParser(description="Go2 RL Deploy")
    parser.add_argument("--config", type=str, default=config_path)
    parser.add_argument("--interface", type=str, default=None,
                        help="Override network interface (e.g. eth0)")
    parser.add_argument("--domain", type=int, default=None,
                        help="Override DDS domain ID")
    args = parser.parse_args()

    config = Config(args.config)
    if args.interface:
        config.interface = args.interface
    if args.domain is not None:
        config.domain_id = args.domain

    print(f"Config: interface={config.interface}, domain_id={config.domain_id}")
    print(f"Policy: {config.policy_path}")

    # ---- 初始化 ----
    ctrl = Go2Controller(config)
    ctrl.init_dds()
    ctrl.wait_for_connection()

    kbd = KeyboardReader()
    state = State.ZERO_TORQUE

    # 速度指令
    vx, vy, vyaw = 0.0, 0.0, 0.0
    VEL_STEP = 0.2       # 每次按键增减的速度
    DECAY = 0.92          # 松手后的衰减系数
    DEAD_ZONE = 0.05      # 低于此值归零

    # 注册安全退出
    running = True
    def on_signal(sig, frame):
        nonlocal running
        running = False
    signal.signal(signal.SIGINT, on_signal)

    print("\n" + "=" * 50)
    print("  Go2 RL Deploy — Keyboard Control")
    print("=" * 50)
    print("  1 = Stand Up    2 = Lie Down")
    print("  3 = Toggle RL Walking")
    print("  W/S = Fwd/Back  A/D = Left/Right")
    print("  J/L = Turn      Space = Stop")
    print("  Q/ESC = Safe Exit")
    print("=" * 50 + "\n")

    # ---- 开始零力矩 ----
    print(f"[{state}] Idle. Press '1' to stand up.")

    try:
        while running:
            loop_start = time.perf_counter()

            # ---- 读取键盘 (timeout 足够长以捕获按键) ----
            key = kbd.get_key(timeout=0.01)

            # ---- 读取遥控器 (真机) ----
            rc_start = ctrl.remote.button[KeyMap.start]
            rc_a = ctrl.remote.button[KeyMap.A]
            rc_select = ctrl.remote.button[KeyMap.select]

            # ---- 全局退出 ----
            if key == '\x1b' or key == 'q' or rc_select:
                print("\n[EXIT] Safe shutdown initiated...")
                break

            # ---- 状态机 ----

            if state == State.ZERO_TORQUE:
                # 每帧发送一条零力矩指令 (不调用阻塞方法)
                for i in range(20):
                    ctrl.low_cmd.motor_cmd[i].q = 0.0
                    ctrl.low_cmd.motor_cmd[i].dq = 0.0
                    ctrl.low_cmd.motor_cmd[i].kp = 0.0
                    ctrl.low_cmd.motor_cmd[i].kd = 0.0
                    ctrl.low_cmd.motor_cmd[i].tau = 0.0
                ctrl._send_cmd()

                if key == '1' or rc_start:
                    ctrl.stand_up()
                    state = State.STANDING
                    print(f"[{state}] Press '3' to start RL walking, '2' to lie down.")

            elif state == State.STANDING:
                # PD 保持站立 (单帧)
                ctrl.hold_stand()

                if key == '3' or rc_a:
                    # 重置 RL 上下文
                    ctrl.action[:] = 0
                    ctrl.cmd[:] = 0
                    vx, vy, vyaw = 0.0, 0.0, 0.0
                    state = State.RL_WALKING
                    print(f"[{state}] RL walking active. Use W/S/A/D/J/L to move.")

                elif key == '2':
                    ctrl.lie_down()
                    state = State.ZERO_TORQUE
                    print(f"[{state}] Lying down complete. Press '1' to stand again.")

            elif state == State.RL_WALKING:
                # ---- 键盘速度控制 ----
                pressed = False
                if key == 'w':
                    vx = min(config.max_cmd[0], vx + VEL_STEP)
                    pressed = True
                elif key == 's':
                    vx = max(-config.max_cmd[0], vx - VEL_STEP)
                    pressed = True
                elif key == 'a':
                    vy = min(config.max_cmd[1], vy + VEL_STEP)
                    pressed = True
                elif key == 'd':
                    vy = max(-config.max_cmd[1], vy - VEL_STEP)
                    pressed = True
                elif key == 'j':
                    vyaw = min(config.max_cmd[2], vyaw + VEL_STEP)
                    pressed = True
                elif key == 'l':
                    vyaw = max(-config.max_cmd[2], vyaw - VEL_STEP)
                    pressed = True
                elif key == ' ':
                    vx, vy, vyaw = 0.0, 0.0, 0.0
                    pressed = True

                # 遥控器输入 (真机, 覆盖键盘)
                if abs(ctrl.remote.ly) > 0.1 or abs(ctrl.remote.lx) > 0.1 or abs(ctrl.remote.rx) > 0.1:
                    vx = ctrl.remote.ly * config.max_cmd[0]
                    vy = -ctrl.remote.lx * config.max_cmd[1]
                    vyaw = -ctrl.remote.rx * config.max_cmd[2]
                    pressed = True

                # 松手衰减
                if not pressed:
                    vx *= DECAY
                    vy *= DECAY
                    vyaw *= DECAY

                # 死区
                if abs(vx) < DEAD_ZONE: vx = 0.0
                if abs(vy) < DEAD_ZONE: vy = 0.0
                if abs(vyaw) < DEAD_ZONE: vyaw = 0.0

                ctrl.set_cmd(vx, vy, vyaw)
                ctrl.rl_step()

                # 状态显示 (不换行, 原地刷新)
                sys.stdout.write(
                    f"\r[{state}] vx={vx:+5.2f}  vy={vy:+5.2f}  "
                    f"vyaw={vyaw:+5.2f}    "
                )
                sys.stdout.flush()

                # 切换回站立
                if key == '3' or rc_a:
                    vx, vy, vyaw = 0.0, 0.0, 0.0
                    state = State.STANDING
                    print(f"\n[{state}] Switched back to standing.")

                # 直接趴下
                elif key == '2':
                    vx, vy, vyaw = 0.0, 0.0, 0.0
                    print("\n[State] Decelerating...")
                    ctrl.set_cmd(0, 0, 0)
                    for _ in range(25):  # 0.5s 减速
                        ctrl.rl_step()
                        time.sleep(config.control_dt)
                    ctrl.lie_down()
                    state = State.ZERO_TORQUE
                    print(f"[{state}] Lying down complete.")

            # ---- 控制频率 ----
            elapsed = time.perf_counter() - loop_start
            sleep_time = config.control_dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        print()

        # ---- 安全关机序列 ----
        # 1. 如果在 RL 行走中, 先减速
        if state == State.RL_WALKING:
            print("[Shutdown] Decelerating...")
            ctrl.set_cmd(0, 0, 0)
            for _ in range(50):  # 1s 减速
                ctrl.rl_step()
                time.sleep(config.control_dt)

        # 2. 趴下
        if state in (State.STANDING, State.RL_WALKING):
            try:
                ctrl.lie_down()
            except Exception as e:
                print(f"[Shutdown] Lie-down failed: {e}")

        # 3. 阻尼
        print("[Shutdown] Sending damping...")
        for _ in range(10):
            ctrl.send_damping()
            time.sleep(config.control_dt)

        kbd.restore()
        print("[Shutdown] Complete. Robot is safe.")


if __name__ == "__main__":
    main()
