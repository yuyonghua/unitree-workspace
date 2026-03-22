"""Go2 远程遥控与建图系统 - FastAPI 主应用"""

import argparse
import asyncio
import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from config import DEFAULT_REMOTE, DEFAULT_LOCALSTA, SPEED_LIMITS, WEB_CONFIG
from robot import RobotDriver
from lidar import LidarCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ==================== 全局组件 ====================

app = FastAPI(title="Go2 远程遥控与建图")
robot = RobotDriver()
lidar = LidarCollector()

# 雷达预览队列 (降采样后, 供前端 WebSocket 消费)
lidar_preview_queue: asyncio.Queue = asyncio.Queue(maxsize=30)
lidar.set_preview_queue(lidar_preview_queue)

# CLI 参数将在 startup 时写入
cli_args: dict = {}

# 模板 & 静态文件
templates = Jinja2Templates(directory="templates")


# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ==================== WebSocket: 运控通道 ====================

@app.websocket("/ws/control")
async def ws_control(ws: WebSocket):
    """运控 WebSocket

    收到的消息格式:
      {"x": float, "y": float, "yaw": float}   -- 摇杆移动指令
      {"action": "stand_up"}                      -- 特殊动作
      {"action": "stand_down"}
      {"action": "recovery_stand"}
      {"action": "stop"}
      {"action": "connect"}                       -- 连接机器人
      {"action": "disconnect"}                    -- 断开连接
      {"action": "start_lidar"}                   -- 启动雷达
      {"action": "stop_lidar"}                    -- 停止雷达
    """
    await ws.accept()
    logger.info("运控 WebSocket 已连接")

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "无效 JSON"})
                continue

            resp = await _handle_control_msg(msg)
            await ws.send_json(resp)

    except WebSocketDisconnect:
        logger.info("运控 WebSocket 已断开")
    except Exception as e:
        logger.error(f"运控 WebSocket 异常: {e}")


async def _handle_control_msg(msg: dict) -> dict:
    """分发运控消息"""
    # --- 摇杆移动 ---
    if "x" in msg and "y" in msg and "yaw" in msg:
        x = _clamp(msg["x"], -SPEED_LIMITS["vx"], SPEED_LIMITS["vx"])
        y = _clamp(msg["y"], -SPEED_LIMITS["vy"], SPEED_LIMITS["vy"])
        yaw = _clamp(msg["yaw"], -SPEED_LIMITS["vz"], SPEED_LIMITS["vz"])
        return await robot.move(x, y, yaw)

    action = msg.get("action", "")

    # --- 特殊动作 ---
    if action == "stand_up":
        return await robot.stand_up()
    if action == "stand_down":
        return await robot.stand_down()
    if action == "recovery_stand":
        return await robot.recovery_stand()
    if action == "stop":
        return await robot.stop_move()

    # --- 连接管理 ---
    if action == "connect":
        return await _do_connect()
    if action == "disconnect":
        # 先停雷达
        if lidar.streaming:
            await lidar.stop(robot.conn)
        return await robot.disconnect()

    # --- 雷达管理 ---
    if action == "start_lidar":
        if not robot.connected:
            return {"success": False, "message": "请先连接机器人"}
        return await lidar.start(robot.conn)
    if action == "stop_lidar":
        return await lidar.stop(robot.conn)

    # --- 状态查询 ---
    if action == "status":
        return {
            "success": True,
            "connected": robot.connected,
            "lidar": lidar.get_status(),
        }

    return {"success": False, "message": f"未知指令: {action}"}


async def _do_connect() -> dict:
    """根据 CLI 参数决定连接方式"""
    mode = cli_args.get("mode", "remote")

    if mode == "localsta":
        ip = cli_args.get("ip") or DEFAULT_LOCALSTA["ip"]
        result = await robot.connect_localsta(ip)
    else:
        serial = cli_args.get("serial") or DEFAULT_REMOTE["serial_number"]
        user = cli_args.get("user") or DEFAULT_REMOTE["username"]
        pwd = cli_args.get("pass") or DEFAULT_REMOTE["password"]
        result = await robot.connect_remote(serial, user, pwd)

    # 连接成功后自动切 normal 模式
    if result.get("success"):
        await asyncio.sleep(1)
        await robot.switch_to_normal()

    return result


# ==================== WebSocket: 雷达预览通道 ====================

@app.websocket("/ws/lidar")
async def ws_lidar(ws: WebSocket):
    """雷达预览 WebSocket

    推送格式: [[x, y], [x, y], ...]  (降采样后的 2D 散点)
    """
    await ws.accept()
    logger.info("雷达预览 WebSocket 已连接")

    try:
        while True:
            try:
                # 等待队列数据, 超时 5 秒发心跳
                points = await asyncio.wait_for(
                    lidar_preview_queue.get(), timeout=5.0
                )
                await ws.send_json({"type": "points", "data": points})
            except asyncio.TimeoutError:
                # 发送心跳保持连接
                await ws.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        logger.info("雷达预览 WebSocket 已断开")
    except Exception as e:
        logger.error(f"雷达预览 WebSocket 异常: {e}")


# ==================== 工具函数 ====================

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


# ==================== CLI 入口 ====================

def parse_args():
    parser = argparse.ArgumentParser(description="Go2 远程遥控与建图系统")
    parser.add_argument("--mode", choices=["remote", "localsta"], default="remote",
                        help="连接模式 (默认: remote)")
    parser.add_argument("--serial", default=None, help="Remote 模式: 序列号")
    parser.add_argument("--user", default=None, help="Remote 模式: 账号")
    parser.add_argument("--pass", dest="pass_", default=None, help="Remote 模式: 密码")
    parser.add_argument("--ip", default=None, help="LocalSTA 模式: 机器人 IP")
    parser.add_argument("--port", type=int, default=None, help="Web 服务端口")
    return parser.parse_args()


if __name__ == "__main__":
    import uvicorn

    args = parse_args()
    cli_args = {
        "mode": args.mode,
        "serial": args.serial,
        "user": args.user,
        "pass": args.pass_,
        "ip": args.ip,
    }

    port = args.port or WEB_CONFIG["port"]
    host = WEB_CONFIG["host"]

    logger.info(f"启动 Go2 远程遥控系统 | 模式={args.mode} | http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
