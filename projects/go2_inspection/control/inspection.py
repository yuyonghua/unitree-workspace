import time
import numpy as np


class InspectionController:

    def __init__(self, tolerance=0.2, scan_duration=2.0):
        self.tolerance = tolerance
        self.scan_duration = scan_duration
        self.waypoints = []
        self.current_index = 0
        self.active = False
        self.scanning = False
        self.scan_start_time = 0

    def set_waypoints(self, waypoints):
        self.waypoints = waypoints
        self.current_index = 0

    def start(self):
        if not self.waypoints:
            return False
        self.active = True
        self.current_index = 0
        return True

    def stop(self):
        self.active = False
        self.scanning = False

    def update(self, robot_pos):
        if not self.active:
            return {"action": "idle"}

        if self.scanning:
            elapsed = time.time() - self.scan_start_time
            if elapsed >= self.scan_duration:
                self.scanning = False
                self.current_index += 1
                if self.current_index >= len(self.waypoints):
                    self.active = False
                    return {"action": "complete"}
            return {"action": "scanning", "progress": elapsed / self.scan_duration}

        if self.current_index >= len(self.waypoints):
            self.active = False
            return {"action": "complete"}

        target = self.waypoints[self.current_index]
        dx = target[0] - robot_pos["x"]
        dy = target[1] - robot_pos["y"]
        dist = np.sqrt(dx * dx + dy * dy)

        if dist < self.tolerance:
            self.scanning = True
            self.scan_start_time = time.time()
            return {"action": "scan_start", "waypoint": self.current_index}

        angle = np.arctan2(dy, dx) - robot_pos.get("yaw", 0)
        vx = 0.5 * np.cos(angle)
        vy = 0.5 * np.sin(angle)
        yaw = np.clip(angle, -1, 1)

        return {"action": "move", "vx": vx, "vy": vy, "yaw": yaw, "distance": dist}

    def get_status(self):
        return {
            "active": self.active,
            "scanning": self.scanning,
            "current_waypoint": self.current_index,
            "total_waypoints": len(self.waypoints),
            "progress": self.current_index / max(len(self.waypoints), 1),
        }
