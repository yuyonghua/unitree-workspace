import numpy as np


class OccupancyGrid:

    def __init__(self, resolution=0.05, width=200, height=200, origin_x=-5.0, origin_y=-5.0):
        self.resolution = resolution
        self.width = width
        self.height = height
        self.origin = {"x": origin_x, "y": origin_y, "z": 0}
        self.grid = np.full((height, width), 0.5, dtype=np.float32)
        self.occupied_prob = 0.9
        self.free_prob = 0.1
        self.lodds_occupied = np.log(self.occupied_prob / (1 - self.occupied_prob))
        self.lodds_free = np.log(self.free_prob / (1 - self.free_prob))

    def world_to_grid(self, x, y):
        gx = int((x - self.origin["x"]) / self.resolution)
        gy = int((y - self.origin["y"]) / self.resolution)
        return gx, gy

    def grid_to_world(self, gx, gy):
        x = gx * self.resolution + self.origin["x"]
        y = gy * self.resolution + self.origin["y"]
        return x, y

    def in_bounds(self, gx, gy):
        return 0 <= gx < self.width and 0 <= gy < self.height

    def update_occupied(self, x, y):
        gx, gy = self.world_to_grid(x, y)
        if self.in_bounds(gx, gy):
            odds = self.grid[gy, gx] / (1 - self.grid[gy, gx] + 1e-6)
            odds *= np.exp(self.lodds_occupied)
            self.grid[gy, gx] = np.clip(odds / (1 + odds), 0, 1)

    def update_free(self, robot_x, robot_y):
        gx, gy = self.world_to_grid(robot_x, robot_y)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                nx, ny = gx + dx, gy + dy
                if self.in_bounds(nx, ny):
                    odds = self.grid[ny, nx] / (1 - self.grid[ny, nx] + 1e-6)
                    odds *= np.exp(self.lodds_free)
                    self.grid[ny, nx] = np.clip(odds / (1 + odds), 0, 1)

    def get_grid(self):
        return self.grid

    def to_image(self):
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img[self.grid > 0.65] = [0, 0, 0]
        img[self.grid < 0.35] = [255, 255, 255]
        img[(self.grid >= 0.35) & (self.grid <= 0.65)] = [128, 128, 128]
        return img
