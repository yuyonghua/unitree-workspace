import threading
import time
import numpy as np
import mujoco


class MuJoCoSimulator:

    def __init__(self, model_path, scene_path=None):
        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.fps = 500
        self.control_cmd = {"vx": 0, "vy": 0, "yaw": 0}
        self.state = {
            "time": 0,
            "position": {"x": 0, "y": 0, "z": 0},
            "orientation": {"w": 1, "x": 0, "y": 0, "z": 0},
            "velocity": {"x": 0, "y": 0, "z": 0},
            "yaw": 0,
        }
        mujoco.mj_resetData(self.model, self.data)

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
        ctrl = self.data.ctrl
        cmd = self.control_cmd
        base_addr = 0
        for i in range(min(12, self.model.nu)):
            ctrl[base_addr + i] = 0
        if self.model.nu > 0:
            ctrl[0] = cmd["vx"] * 500
        if self.model.nu > 1:
            ctrl[1] = cmd["vy"] * 500
        if self.model.nu > 2:
            ctrl[2] = cmd["yaw"] * 50

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
            if self.model.nq >= 3:
                self.data.qpos[2] = 0.35

    def stand_down(self):
        with self.lock:
            if self.model.nq >= 3:
                self.data.qpos[2] = 0.15

    def stop_movement(self):
        self.set_control(0, 0, 0)
