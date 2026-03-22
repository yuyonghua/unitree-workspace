import asyncio
import json
import os
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SIMULATION, LIDAR, MAPPING, WEB, ROBOT
from sim.simulator import MuJoCoSimulator
from sim.lidar import LiDARSensor
from mapping.mapper import OccupancyMapper
from storage.manager import MapManager

app = FastAPI(title="Go2 Inspection System")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

simulator = None
lidar = None
mapper = None
map_manager = None
connected_clients = set()


def init_system():
    global simulator, lidar, mapper, map_manager
    model_path = os.path.join(os.path.dirname(__file__), SIMULATION["model_path"])
    if not os.path.exists(model_path):
        model_path = os.path.join(
            os.path.dirname(__file__),
            "../../git/official/unitree_mujoco/unitree_robots/go2/go2.xml"
        )
    simulator = MuJoCoSimulator(model_path)
    lidar = LiDARSensor(
        horizontal_fov=LIDAR["horizontal_fov"],
        resolution=LIDAR["horizontal_resolution"],
        max_range=LIDAR["max_range"],
        min_range=LIDAR["min_range"],
    )
    mapper = OccupancyMapper(
        resolution=MAPPING["resolution"],
        width=MAPPING["width"],
        height=MAPPING["height"],
        origin_x=MAPPING["origin_x"],
        origin_y=MAPPING["origin_y"],
    )
    map_manager = MapManager()


@app.on_event("startup")
async def startup():
    init_system()


@app.on_event("shutdown")
async def shutdown():
    if simulator:
        simulator.stop()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/connect")
async def api_connect():
    if simulator:
        simulator.start()
        return {"success": True, "message": "仿真已启动"}
    return {"success": False, "message": "仿真器未初始化"}


@app.post("/api/disconnect")
async def api_disconnect():
    if simulator:
        simulator.stop()
        return {"success": True, "message": "仿真已停止"}
    return {"success": False, "message": "仿真器未初始化"}


@app.post("/api/stand_up")
async def api_stand_up():
    if simulator:
        simulator.stand_up()
        return {"success": True, "message": "站起"}
    return {"success": False, "message": "仿真器未初始化"}


@app.post("/api/stand_down")
async def api_stand_down():
    if simulator:
        simulator.stand_down()
        return {"success": True, "message": "趴下"}
    return {"success": False, "message": "仿真器未初始化"}


@app.post("/api/stop")
async def api_stop():
    if simulator:
        simulator.stop_movement()
        return {"success": True, "message": "停止移动"}
    return {"success": False, "message": "仿真器未初始化"}


@app.post("/api/move")
async def api_move(vx: float = 0, vy: float = 0, yaw: float = 0):
    if simulator:
        simulator.set_control(
            max(min(vx, ROBOT["max_velocity_x"]), -ROBOT["max_velocity_x"]),
            max(min(vy, ROBOT["max_velocity_y"]), -ROBOT["max_velocity_y"]),
            max(min(yaw, ROBOT["max_yaw_rate"]), -ROBOT["max_yaw_rate"]),
        )
        return {"success": True, "message": f"移动: vx={vx}, vy={vy}, yaw={yaw}"}
    return {"success": False, "message": "仿真器未初始化"}


@app.get("/api/status")
async def api_status():
    if simulator:
        return {"success": True, "data": simulator.get_state()}
    return {"success": False, "message": "仿真器未初始化"}


@app.post("/api/map/start_mapping")
async def api_start_mapping():
    if mapper:
        mapper.start()
        return {"success": True, "message": "开始建图"}
    return {"success": False, "message": "建图器未初始化"}


@app.post("/api/map/stop_mapping")
async def api_stop_mapping():
    if mapper:
        mapper.stop()
        return {"success": True, "message": "停止建图", "scan_count": mapper.scan_count}
    return {"success": False, "message": "建图器未初始化"}


@app.post("/api/map/save")
async def api_save_map(name: str = "default"):
    if mapper and map_manager:
        map_data = mapper.get_map_data()
        filepath = map_manager.save_map(name, map_data)
        return {"success": True, "message": f"地图已保存: {name}", "path": filepath}
    return {"success": False, "message": "建图器或存储管理器未初始化"}


@app.get("/api/map/list")
async def api_list_maps():
    if map_manager:
        return {"success": True, "data": map_manager.list_maps()}
    return {"success": False, "message": "存储管理器未初始化"}


@app.post("/api/map/load/{name}")
async def api_load_map(name: str):
    if map_manager:
        map_data = map_manager.load_map(name)
        if map_data:
            return {"success": True, "data": map_data}
        return {"success": False, "message": f"地图不存在: {name}"}
    return {"success": False, "message": "存储管理器未初始化"}


@app.delete("/api/map/delete/{name}")
async def api_delete_map(name: str):
    if map_manager:
        if map_manager.delete_map(name):
            return {"success": True, "message": f"地图已删除: {name}"}
        return {"success": False, "message": f"地图不存在: {name}"}
    return {"success": False, "message": "存储管理器未初始化"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            if simulator and simulator.running:
                state = simulator.get_state()
                lidar_data = None
                if lidar:
                    lidar_data = lidar.scan(simulator.model, simulator.data, state.get("yaw", 0))
                    if mapper and mapper.is_active():
                        mapper.add_scan(lidar_data)
                await websocket.send_json({
                    "type": "state",
                    "data": state,
                    "lidar": lidar_data,
                    "mapping_active": mapper.is_active() if mapper else False,
                })
            await asyncio.sleep(1.0 / SIMULATION["web_fps"])
    except WebSocketDisconnect:
        connected_clients.discard(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=WEB["host"], port=WEB["port"])
