import numpy as np
from .occupancy_grid import OccupancyGrid


class OccupancyMapper:

    def __init__(self, resolution=0.05, width=200, height=200, origin_x=-5.0, origin_y=-5.0):
        self.grid = OccupancyGrid(resolution, width, height, origin_x, origin_y)
        self.active = False
        self.scan_count = 0
        self.accumulated_points = []

    def start(self):
        self.active = True
        self.scan_count = 0
        self.accumulated_points = []

    def stop(self):
        self.active = False

    def add_scan(self, lidar_data):
        if not self.active:
            return

        self.scan_count += 1
        robot_x = lidar_data["robot_pose"]["x"]
        robot_y = lidar_data["robot_pose"]["y"]
        robot_yaw = lidar_data["robot_pose"]["yaw"]

        cos_yaw = np.cos(robot_yaw)
        sin_yaw = np.sin(robot_yaw)

        for point in lidar_data["points"]:
            world_x = robot_x + point[0] * cos_yaw - point[1] * sin_yaw
            world_y = robot_y + point[0] * sin_yaw + point[1] * cos_yaw
            self.accumulated_points.append([world_x, world_y])
            self.grid.update_occupied(world_x, world_y)

        self.grid.update_free(robot_x, robot_y)

    def get_map_data(self):
        return {
            "resolution": self.grid.resolution,
            "width": self.grid.width,
            "height": self.grid.height,
            "origin": self.grid.origin,
            "data": self.grid.get_grid().tolist(),
            "scan_count": self.scan_count,
            "points": self.accumulated_points,
        }

    def get_2d_image(self):
        return self.grid.to_image()

    def is_active(self):
        return self.active
