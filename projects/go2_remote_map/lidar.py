"""Go2 远程遥控与建图系统 - 雷达双路分发 (落盘 + 降采样推送)"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any

import numpy as np

from config import LIDAR_CONFIG, DATA_DIR

logger = logging.getLogger(__name__)


class LidarCollector:
    """雷达数据双路分发：
    - 旁路1: 原始高精度数据落盘 (JSONL + PCD)
    - 旁路2: 极端降采样后通过 Queue 推送给前端 WebSocket
    """

    def __init__(self):
        self.streaming = False
        self.frame_count = 0
        self._preview_queue: Optional[asyncio.Queue] = None

        # 落盘文件句柄
        self._jsonl_fp = None
        self._pcd_fp = None
        self._session_prefix = ""
        self._pcd_point_count = 0

        # 配置
        self._downsample_rate = LIDAR_CONFIG.get("downsample_rate", 50)
        self._max_preview = LIDAR_CONFIG.get("max_preview_points", 2000)
        self._skip_frames = LIDAR_CONFIG.get("skip_frames", 1)

    def set_preview_queue(self, q: asyncio.Queue):
        """设置前端预览用的异步队列"""
        self._preview_queue = q

    # ==================== 启动 / 停止 ====================

    async def start(self, conn) -> Dict[str, Any]:
        """启动雷达数据采集"""
        if self.streaming:
            return {"success": True, "message": "雷达已在运行"}

        try:
            # 确保落盘目录存在
            os.makedirs(DATA_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._session_prefix = os.path.join(DATA_DIR, f"session_{ts}")

            # 打开落盘文件
            self._jsonl_fp = open(f"{self._session_prefix}.jsonl", "a")
            self._init_pcd_file()

            # 禁用流量节省
            await conn.datachannel.disableTrafficSaving(True)

            # 设置解码器
            decoder = LIDAR_CONFIG.get("decoder", "native")
            conn.datachannel.set_decoder(decoder_type=decoder)

            # 开启雷达
            conn.datachannel.pub_sub.publish_without_callback("rt/utlidar/switch", "on")

            # 订阅压缩点云
            conn.datachannel.pub_sub.subscribe(
                "rt/utlidar/voxel_map_compressed",
                self._on_lidar_data,
            )

            self.streaming = True
            logger.info(f"雷达已启动, 落盘前缀: {self._session_prefix}")
            return {"success": True, "message": "雷达已启动"}

        except Exception as e:
            logger.error(f"雷达启动失败: {e}")
            return {"success": False, "message": str(e)}

    async def stop(self, conn) -> Dict[str, Any]:
        """停止雷达数据采集"""
        try:
            if conn:
                conn.datachannel.pub_sub.publish_without_callback("rt/utlidar/switch", "off")
            self.streaming = False
            self._close_files()
            logger.info(f"雷达已停止, 共采集 {self.frame_count} 帧")
            return {"success": True, "message": f"已停止, 共 {self.frame_count} 帧"}
        except Exception as e:
            logger.error(f"雷达停止失败: {e}")
            return {"success": False, "message": str(e)}

    def get_status(self) -> Dict[str, Any]:
        return {
            "streaming": self.streaming,
            "frame_count": self.frame_count,
            "pcd_points": self._pcd_point_count,
            "session": self._session_prefix,
        }

    # ==================== 数据回调 ====================

    def _on_lidar_data(self, message: dict):
        """雷达订阅回调 — 在 WebRTC 事件循环中调用"""
        self.frame_count += 1

        try:
            points = self._extract_points(message)
            if points is None or len(points) == 0:
                return
        except Exception as e:
            logger.error(f"解析雷达数据失败: {e}")
            return

        # --- 旁路1: 落盘 ---
        try:
            self._save_jsonl(points)
            self._save_pcd(points)
        except Exception as e:
            logger.error(f"落盘失败: {e}")

        # --- 旁路2: 降采样推送到前端 ---
        if self.frame_count % self._skip_frames != 0:
            return

        try:
            preview = self._downsample_for_preview(points)
            if self._preview_queue and not self._preview_queue.full():
                self._preview_queue.put_nowait(preview)
        except Exception:
            pass  # 队列满则丢弃该帧

    # ==================== 点云解析 ====================

    def _extract_points(self, message: dict) -> Optional[np.ndarray]:
        """从订阅消息中提取 Nx3 点云数组"""
        data = message.get("data", {})
        voxel_data = data.get("data", {})

        # native decoder 输出: {"points": ndarray (N,3) float64}
        if "points" in voxel_data and isinstance(voxel_data["points"], np.ndarray):
            return voxel_data["points"]

        # libvoxel decoder 输出: {"positions": ndarray uint8, ...}
        positions = voxel_data.get("positions", None)
        if positions is not None:
            if isinstance(positions, np.ndarray):
                arr = positions
            else:
                arr = np.array(list(positions))
            # positions 是 uint8, 每 3 个为一组 (x,y,z)
            if len(arr) % 3 != 0:
                return None
            # 先转 float 再归一化: 宇树体素 positions 是 0-255 映射到实际坐标
            # 这里简单还原 (实际范围取决于体素配置)
            points = arr.reshape(-1, 3).astype(np.float32)
            return points

        # 兜底: 尝试直接从 data 中读取 points
        raw_points = data.get("points", None)
        if raw_points is not None:
            if isinstance(raw_points, np.ndarray):
                return raw_points
            return np.array(raw_points, dtype=np.float32).reshape(-1, 3)

        return None

    # ==================== 落盘逻辑 ====================

    def _save_jsonl(self, points: np.ndarray):
        """追加写入 JSONL 文件"""
        if not self._jsonl_fp:
            return
        record = {
            "ts": time.time(),
            "frame": self.frame_count,
            "points": points.tolist(),
        }
        self._jsonl_fp.write(json.dumps(record, separators=(",", ":")) + "\n")
        self._jsonl_fp.flush()

    def _init_pcd_file(self):
        """初始化 PCD 文件 (ASCII 格式 header)"""
        pcd_path = f"{self._session_prefix}.pcd"
        self._pcd_fp = open(pcd_path, "a")
        # 写 PCD header (先写占位, 停止时更新)
        header = (
            "# .PCD v0.7 - Point Cloud Data file format\n"
            "VERSION 0.7\n"
            "FIELDS x y z\n"
            "SIZE 4 4 4\n"
            "TYPE F F F\n"
            "COUNT 1 1 1\n"
            "WIDTH 0\n"
            "HEIGHT 1\n"
            "VIEWPOINT 0 0 0 1 0 0 0\n"
            "POINTS 0\n"
            "DATA ascii\n"
        )
        self._pcd_fp.write(header)
        self._pcd_fp.flush()

    def _save_pcd(self, points: np.ndarray):
        """追加点云到 PCD 文件 (ASCII DATA)"""
        if not self._pcd_fp:
            return
        for pt in points:
            self._pcd_fp.write(f"{pt[0]:.6f} {pt[1]:.6f} {pt[2]:.6f}\n")
        self._pcd_point_count += len(points)
        # 每 100 帧 flush 一次
        if self.frame_count % 100 == 0:
            self._pcd_fp.flush()

    def _close_files(self):
        """关闭落盘文件, 并修正 PCD header 中的点数"""
        if self._jsonl_fp:
            self._jsonl_fp.close()
            self._jsonl_fp = None

        if self._pcd_fp:
            self._pcd_fp.close()
            self._pcd_fp = None

            # 回写 PCD header 中的实际点数
            pcd_path = f"{self._session_prefix}.pcd"
            try:
                with open(pcd_path, "r") as f:
                    content = f.read()
                content = content.replace("WIDTH 0", f"WIDTH {self._pcd_point_count}")
                content = content.replace("POINTS 0", f"POINTS {self._pcd_point_count}")
                with open(pcd_path, "w") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"修正 PCD header 失败: {e}")

    # ==================== 降采样 ====================

    def _downsample_for_preview(self, points: np.ndarray) -> List[List[float]]:
        """极端降采样: 均匀抽点 + 丢弃 Z 轴, 返回 [[x, y], ...]"""
        n = len(points)
        if n == 0:
            return []

        step = max(1, n // self._max_preview)
        sampled = points[::step]

        # 丢弃 Z 轴, 保留 x, y
        flat = sampled[:, :2].tolist()

        # 再次截断保证上限
        if len(flat) > self._max_preview:
            flat = flat[: self._max_preview]

        return flat
