import numpy as np


class LiDARSensor:

    def __init__(self, horizontal_fov=140, resolution=0.5, max_range=10.0, min_range=0.1):
        self.horizontal_fov = horizontal_fov
        self.resolution = resolution
        self.max_range = max_range
        self.min_range = min_range
        self.num_rays = int(horizontal_fov / resolution)
        self.angles = np.linspace(
            -np.radians(horizontal_fov / 2),
            np.radians(horizontal_fov / 2),
            self.num_rays,
        )

    def scan(self, model, data, robot_yaw=0):
        points = []
        robot_x = data.qpos[0] if model.nq >= 1 else 0
        robot_y = data.qpos[1] if model.nq >= 2 else 0

        for angle in self.angles:
            world_angle = angle + robot_yaw
            dist = self._raycast(model, data, robot_x, robot_y, world_angle)
            if dist is not None:
                local_x = dist * np.cos(angle)
                local_y = dist * np.sin(angle)
                points.append([local_x, local_y])

        return {
            "timestamp": float(data.time),
            "robot_pose": {"x": robot_x, "y": robot_y, "yaw": robot_yaw},
            "points": points,
        }

    def _raycast(self, model, data, x, y, angle):
        for dist in np.arange(self.min_range, self.max_range, 0.05):
            px = x + dist * np.cos(angle)
            py = y + dist * np.sin(angle)
            if self._is_collision(model, data, px, py):
                return dist
        return None

    def _is_collision(self, model, data, x, y):
        for i in range(model.nbody):
            if model.body_geomadr[i] >= 0:
                geom_pos = data.geom_xpos[model.body_geomadr[i]]
                geom_size = model.geom_size[model.body_geomadr[i]]
                dx = x - geom_pos[0]
                dy = y - geom_pos[1]
                dist = np.sqrt(dx * dx + dy * dy)
                if dist < (geom_size[0] if len(geom_size) > 0 else 0.5) + 0.1:
                    return True
        return False
