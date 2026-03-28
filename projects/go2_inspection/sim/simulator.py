import threading
import time
import numpy as np
import mujoco


class MuJoCoSimulator:

    def __init__(self, model_path):
        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.fps = 500

        self.control_cmd = {"vx": 0, "vy": 0, "yaw": 0}
        self.mode = "stand"

        self.stand_qpos = np.array([0, 0.9, -1.8] * 4)
        self.down_qpos = np.array([0, 1.2, -2.4] * 4)
        self.target_qpos = self.stand_qpos.copy()
        self.kp = 80.0
        self.kd = 2.0

        self.state = {
            "time": 0,
            "position": {"x": 0, "y": 0, "z": 0},
            "orientation": {"w": 1, "x": 0, "y": 0, "z": 0},
            "velocity": {"x": 0, "y": 0, "z": 0},
            "yaw": 0,
        }

        mujoco.mj_resetData(self.model, self.data)
        self._set_initial_pose()

    def _set_initial_pose(self):
        if self.model.nq >= 19:
            self.data.qpos[2] = 0.27
            self.data.qpos[3] = 1
            for i in range(12):
                self.data.qpos[7 + i] = self.stand_qpos[i]
        mujoco.mj_forward(self.model, self.data)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None

    def _run_loop(self):
        dt = 1.0 / self.fps
        while self.running:
            start = time.time()
            with self.lock:
                self._apply_control()
                mujoco.mj_step(self.model, self.data)
                self._update_state()
            elapsed = time.time() - start
            if elapsed < dt:
                time.sleep(dt - elapsed)

    def _apply_control(self):
        nu = self.model.nu
        if nu < 12:
            return

        ctrl = self.data.ctrl
        cmd = self.control_cmd

        for i in range(12):
            q = self.data.qpos[7 + i] if self.model.nq > 7 + i else 0
            dq = self.data.qvel[6 + i] if self.model.nv > 6 + i else 0
            tau = self.kp * (self.target_qpos[i] - q) + self.kd * (0 - dq)
            ctrl[i] = np.clip(tau, -45, 45)

        if self.mode == "stand":
            if cmd["vx"] != 0 or cmd["vy"] != 0 or cmd["yaw"] != 0:
                fx = cmd["vx"] * 200
                fy = cmd["vy"] * 200
                tz = cmd["yaw"] * 30
                ctrl[0] += tz
                ctrl[3] -= tz
                ctrl[6] += tz
                ctrl[9] -= tz
                ctrl[1] += fx * 0.3
                ctrl[4] += fx * 0.3
                ctrl[7] -= fx * 0.3
                ctrl[10] -= fx * 0.3
                ctrl[2] += fy * 0.3
                ctrl[5] -= fy * 0.3
                ctrl[8] += fy * 0.3
                ctrl[11] -= fy * 0.3

    def _update_state(self):
        self.state["time"] = self.data.time
        if self.model.nq >= 7:
            self.state["position"] = {
                "x": float(self.data.qpos[0]),
                "y": float(self.data.qpos[1]),
                "z": float(self.data.qpos[2]),
            }
            self.state["orientation"] = {
                "w": float(self.data.qpos[3]),
                "x": float(self.data.qpos[4]),
                "y": float(self.data.qpos[5]),
                "z": float(self.data.qpos[6]),
            }
            qw, qx, qy, qz = self.data.qpos[3:7]
            self.state["yaw"] = float(np.arctan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz)))
        if self.model.nv >= 6:
            self.state["velocity"] = {
                "x": float(self.data.qvel[0]),
                "y": float(self.data.qvel[1]),
                "z": float(self.data.qvel[2]),
            }

    def set_control(self, vx, vy, yaw):
        with self.lock:
            self.control_cmd = {"vx": vx, "vy": vy, "yaw": yaw}

    def get_state(self):
        with self.lock:
            return dict(self.state)

    def stand_up(self):
        with self.lock:
            self.target_qpos = self.stand_qpos.copy()
            self.mode = "stand"
            self.data.qpos[2] = 0.27

    def stand_down(self):
        with self.lock:
            self.target_qpos = self.down_qpos.copy()
            self.mode = "stand"
            self.data.qpos[2] = 0.12

    def stop_movement(self):
        self.set_control(0, 0, 0)
