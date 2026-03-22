import json
import os
import time


class MapManager:

    def __init__(self, map_dir="storage/maps"):
        self.map_dir = map_dir
        os.makedirs(map_dir, exist_ok=True)

    def save_map(self, name, map_data):
        filename = f"{name}.json"
        filepath = os.path.join(self.map_dir, filename)
        data = {
            "version": "1.0",
            "type": "occupancy_grid",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "name": name,
            "metadata": {
                "resolution": map_data["resolution"],
                "width": map_data["width"],
                "height": map_data["height"],
                "origin": map_data["origin"],
                "robot_model": "go2",
            },
            "data": map_data["data"],
            "scan_count": map_data["scan_count"],
        }
        with open(filepath, "w") as f:
            json.dump(data, f)
        return filepath

    def load_map(self, name):
        filename = f"{name}.json"
        filepath = os.path.join(self.map_dir, filename)
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r") as f:
            return json.load(f)

    def list_maps(self):
        maps = []
        for filename in os.listdir(self.map_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.map_dir, filename)
                stat = os.stat(filepath)
                maps.append({
                    "name": filename[:-5],
                    "size": stat.st_size,
                    "created_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%S", time.localtime(stat.st_mtime)
                    ),
                })
        return sorted(maps, key=lambda x: x["created_at"], reverse=True)

    def delete_map(self, name):
        filename = f"{name}.json"
        filepath = os.path.join(self.map_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
