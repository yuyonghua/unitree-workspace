"""Go2 远程遥控与建图系统 - WebRTC 连接与运动控制"""

import asyncio
import logging
from typing import Optional, Dict, Any

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

logger = logging.getLogger(__name__)


class RobotDriver:
    """封装 WebRTC 连接与运动控制"""

    def __init__(self):
        self.conn: Optional[UnitreeWebRTCConnection] = None
        self.connected = False

    # ==================== 连接管理 ====================

    async def connect_remote(self, serial: str, username: str, password: str) -> Dict[str, Any]:
        """Remote 模式连接（经 TURN 服务器）"""
        try:
            self.conn = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.Remote,
                serialNumber=serial,
                username=username,
                password=password,
            )
            logger.info("正在通过 TURN 服务器连接...")
            await self.conn.connect()
            if not self.conn.isConnected:
                return {"success": False, "message": "连接建立但握手失败"}
            self.connected = True
            logger.info(f"已远程连接到 {serial}")
            return {"success": True, "message": f"已连接到 {serial}"}
        except Exception as e:
            logger.error(f"Remote 连接失败: {e}")
            return {"success": False, "message": str(e)}

    async def connect_localsta(self, ip: str) -> Dict[str, Any]:
        """LocalSTA 模式连接（同局域网）"""
        try:
            self.conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=ip)
            logger.info(f"正在通过局域网连接 {ip}...")
            await self.conn.connect()
            if not self.conn.isConnected:
                return {"success": False, "message": "连接建立但握手失败"}
            self.connected = True
            logger.info(f"已通过局域网连接到 {ip}")
            return {"success": True, "message": f"已连接到 {ip}"}
        except Exception as e:
            logger.error(f"LocalSTA 连接失败: {e}")
            return {"success": False, "message": str(e)}

    async def disconnect(self) -> Dict[str, Any]:
        """断开连接"""
        try:
            if self.conn:
                await self.conn.disconnect()
            self.connected = False
            self.conn = None
            return {"success": True, "message": "已断开"}
        except Exception as e:
            logger.error(f"断开失败: {e}")
            self.connected = False
            self.conn = None
            return {"success": False, "message": str(e)}

    # ==================== 模式切换 ====================

    async def switch_to_normal(self) -> Dict[str, Any]:
        """切换到 normal 运动模式"""
        if not self._check():
            return {"success": False, "message": "未连接"}
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["MOTION_SWITCHER"],
                {"api_id": 1002, "parameter": {"name": "normal"}},
            )
            logger.info("已发送 normal 模式切换指令")
            return {"success": True, "message": "已切换到 normal 模式"}
        except Exception as e:
            logger.error(f"模式切换失败: {e}")
            return {"success": False, "message": str(e)}

    # ==================== 运动控制 ====================

    async def move(self, x: float, y: float, yaw: float) -> Dict[str, Any]:
        """发送持续移动指令 (Move api_id=1008)

        x:   前后速度 (正=前)
        y:   左右速度 (正=左)
        yaw: 旋转速度 (正=逆时针)
        """
        if not self._check():
            return {"success": False, "message": "未连接"}
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["Move"], "parameter": {"x": x, "y": y, "z": yaw}},
            )
            return {"success": True}
        except Exception as e:
            logger.error(f"Move 指令发送失败: {e}")
            return {"success": False, "message": str(e)}

    async def stop_move(self) -> Dict[str, Any]:
        """停止移动"""
        if not self._check():
            return {"success": False, "message": "未连接"}
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD["StopMove"]},
            )
            return {"success": True, "message": "已停止"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def stand_up(self) -> Dict[str, Any]:
        """站起"""
        return await self._simple_action("StandUp", "站起")

    async def stand_down(self) -> Dict[str, Any]:
        """趴下"""
        return await self._simple_action("StandDown", "趴下")

    async def recovery_stand(self) -> Dict[str, Any]:
        """恢复站立"""
        return await self._simple_action("RecoveryStand", "恢复站立")

    # ==================== 内部工具 ====================

    def _check(self) -> bool:
        return self.connected and self.conn is not None and self.conn.isConnected

    async def _simple_action(self, cmd_name: str, label: str) -> Dict[str, Any]:
        if not self._check():
            return {"success": False, "message": "未连接"}
        try:
            await self.conn.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {"api_id": SPORT_CMD[cmd_name]},
            )
            logger.info(f"{label} 指令已发送")
            return {"success": True, "message": f"{label} 指令已发送"}
        except Exception as e:
            logger.error(f"{label} 失败: {e}")
            return {"success": False, "message": str(e)}
