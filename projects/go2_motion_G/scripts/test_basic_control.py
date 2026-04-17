"""
Phase 1 基础控制测试。

参考官方 unitree_mujoco/example/python/stand_go2.py。
关键参数:
  - 控制频率 500Hz (dt=0.002s)，与仿真器 timestep 匹配
  - CRC 校验始终需要
  - kp=50, kd=3.5 (官方站立参数)

使用方法:
  终端1 (启动仿真器):
    cd ~/unitree-workspace/git/official/unitree_mujoco/simulate_python
    python unitree_mujoco.py
  
  终端2 (运行本测试):
    cd ~/unitree-workspace/projects/go2_motion_G
    python scripts/test_basic_control.py
"""

import sys
import os
import time
import numpy as np

# 添加项目根目录到 path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from go2_motion.config import Go2Config
from go2_motion.comm.dds_comm import DDSComm


# 官方站立角度 (来自 stand_go2.py)
STAND_UP_JOINT_POS = np.array([
    0.00571868, 0.608813, -1.21763,
    -0.00571868, 0.608813, -1.21763,
    0.00571868, 0.608813, -1.21763,
    -0.00571868, 0.608813, -1.21763,
], dtype=np.float32)

STAND_DOWN_JOINT_POS = np.array([
    0.0473455, 1.22187, -2.44375,
    -0.0473455, 1.22187, -2.44375,
    0.0473455, 1.22187, -2.44375,
    -0.0473455, 1.22187, -2.44375,
], dtype=np.float32)


def print_state(state, prefix=""):
    """打印机器人状态摘要"""
    print(f"{prefix}[tick={state.tick}]")
    print(f"  Motor Q (rad): {state.motor_q.round(4)}")
    print(f"  Motor Q (deg): {np.degrees(state.motor_q).round(1)}")
    print(f"  IMU Quat: {state.imu_quaternion.round(4)}")
    print(f"  IMU Gyro: {state.imu_gyroscope.round(4)}")


def main():
    # 加载仿真配置
    config_path = os.path.join(PROJECT_ROOT, "configs", "go2_sim.yaml")
    config = Go2Config.from_yaml(config_path)
    print(f"Loaded config: {config}")

    # 初始化 DDS 通信
    comm = DDSComm(config)
    comm.init()

    # 等待连接
    print("\nWaiting for connection to simulator...")
    if not comm.wait_for_connection(timeout=15.0):
        print("ERROR: Failed to connect to simulator!")
        sys.exit(1)

    # 等一小段时间让状态稳定
    time.sleep(0.5)

    # 读取初始状态
    print("\n=== Initial State ===")
    state = comm.get_state()
    print_state(state)

    # ===== Phase 1: 站立 (参考 stand_go2.py) =====
    # 控制频率 500Hz (dt=0.002s)，持续 3 秒完成站立
    dt = 0.002  # 500Hz，与仿真器 timestep 匹配
    running_time = 0.0
    standup_duration = 3.0  # 站立持续时间 (s)

    print(f"\n=== Standing up (500Hz, {standup_duration}s) ===")
    print(f"Target stand-up angles (deg): {np.degrees(STAND_UP_JOINT_POS).round(1)}")

    while running_time < standup_duration:
        step_start = time.perf_counter()
        running_time += dt

        # tanh 平滑过渡 (与官方 stand_go2.py 一致)
        phase = np.tanh(running_time / 1.2)

        target_q = phase * STAND_UP_JOINT_POS + (1 - phase) * STAND_DOWN_JOINT_POS
        kps = np.full(12, phase * 50.0 + (1 - phase) * 20.0, dtype=np.float32)
        kds = np.full(12, 3.5, dtype=np.float32)

        comm.send_position_cmd(target_q=target_q, kps=kps, kds=kds)

        # 每 0.5 秒打印一次状态
        if int(running_time / 0.5) != int((running_time - dt) / 0.5):
            state = comm.get_state()
            q_err = np.degrees(np.abs(state.motor_q - target_q))
            print(
                f"  [t={running_time:.1f}s phase={phase:.2f}] "
                f"q[0]={state.motor_q[0]:.4f} target={target_q[0]:.4f} "
                f"max_err={q_err.max():.1f}° tick={state.tick}"
            )

        time_until_next = dt - (time.perf_counter() - step_start)
        if time_until_next > 0:
            time.sleep(time_until_next)

    print("Stand-up complete!")

    # 打印站立后的状态
    time.sleep(0.2)
    state = comm.get_state()
    print("\n=== Post-standup State ===")
    print_state(state)

    # ===== Phase 2: 保持站立 (使用 RL 默认角度) =====
    print("\n=== Switching to RL default angles and holding (press Ctrl+C to stop) ===")
    print(f"RL default angles (deg): {np.degrees(config.default_angles).round(1)}")

    # 先从当前站立角度过渡到 RL 默认角度 (2 秒)
    transition_time = 0.0
    transition_duration = 2.0
    while transition_time < transition_duration:
        step_start = time.perf_counter()
        transition_time += dt

        phase = np.tanh(transition_time / 1.0)
        target_q = phase * config.default_angles + (1 - phase) * STAND_UP_JOINT_POS
        kps = np.full(12, 50.0, dtype=np.float32)
        kds = np.full(12, 3.5, dtype=np.float32)

        comm.send_position_cmd(target_q=target_q, kps=kps, kds=kds)

        if int(transition_time / 0.5) != int((transition_time - dt) / 0.5):
            state = comm.get_state()
            print(
                f"  [transition t={transition_time:.1f}s] q[0]={state.motor_q[0]:.4f}"
            )

        time_until_next = dt - (time.perf_counter() - step_start)
        if time_until_next > 0:
            time.sleep(time_until_next)

    print("Transition to RL default angles complete!")

    # Phase 3: 持续发送 RL 默认角度保持站立
    try:
        step = 0
        while True:
            step_start = time.perf_counter()

            comm.send_position_cmd(
                target_q=config.default_angles,
                kps=config.kps,
                kds=np.full(12, 3.5, dtype=np.float32),
            )

            # 每 1 秒打印一次状态
            if step % 500 == 0:
                state = comm.get_state()
                q_error = np.abs(state.motor_q - config.default_angles)
                print(
                    f"  [t={step * dt:.1f}s] "
                    f"max_q_error={np.degrees(q_error.max()):.2f}° "
                    f"mean_q_error={np.degrees(q_error.mean()):.2f}° "
                    f"q[0:3]={state.motor_q[:3].round(4)} "
                    f"tick={state.tick}"
                )

            step += 1
            time_until_next = dt - (time.perf_counter() - step_start)
            if time_until_next > 0:
                time.sleep(time_until_next)

    except KeyboardInterrupt:
        print("\n\n=== Stopping - entering damping mode ===")
        # 发送几次阻尼指令确保生效
        for _ in range(100):
            comm.send_damping_cmd()
            time.sleep(dt)
        print("Done. Robot is in damping mode.")


if __name__ == "__main__":
    main()
