import numpy as np


class PathPlanner:

    def __init__(self, grid_resolution=0.05):
        self.resolution = grid_resolution

    def plan_path(self, start, goal, occupancy_grid):
        start_grid = self._world_to_grid(start)
        goal_grid = self._world_to_grid(goal)
        path_grid = self._astar(start_grid, goal_grid, occupancy_grid)
        if path_grid:
            return [self._grid_to_world(p) for p in path_grid]
        return []

    def _world_to_grid(self, pos):
        return (int(pos[0] / self.resolution), int(pos[1] / self.resolution))

    def _grid_to_world(self, pos):
        return (pos[0] * self.resolution, pos[1] * self.resolution)

    def _astar(self, start, goal, grid):
        if not grid:
            return []

        open_set = {start}
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}

        while open_set:
            current = min(open_set, key=lambda x: f_score.get(x, float("inf")))

            if current == goal:
                return self._reconstruct_path(came_from, current)

            open_set.remove(current)

            for neighbor in self._get_neighbors(current, grid):
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    open_set.add(neighbor)

        return []

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _get_neighbors(self, pos, grid):
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid):
                if grid[ny][nx] < 0.65:
                    neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path))
