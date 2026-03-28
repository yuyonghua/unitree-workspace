"""FastAPI + Vuer web server for MuJoCo visualization.

This module provides:
- REST API for simulation control
- WebSocket for real-time state streaming
- Vuer integration for 3D visualization
"""

import sys
import json
import asyncio
import threading
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ROBOTS, SIM_CONFIG, MUJOCO_ROBOTS_DIR
from sim.simulator import MuJoCoSimulator, get_simulator


class SimulationManager:
    """Manages simulation lifecycle and web connections."""

    def __init__(self):
        self.simulator: Optional[MuJoCoSimulator] = None
        self.current_robot: Optional[str] = None
        self.websockets: list[WebSocket] = []
        self.state_broadcast_task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    def start_simulation(self, robot_name: str) -> Dict[str, Any]:
        """Start simulation with specified robot."""
        if robot_name not in ROBOTS:
            return {"success": False, "error": f"Unknown robot: {robot_name}"}

        # Stop existing simulation
        if self.simulator:
            self.simulator.stop()

        # Create new simulator
        robot_config = ROBOTS[robot_name]
        self.simulator = MuJoCoSimulator(robot_config, SIM_CONFIG)

        try:
            self.simulator.load_model()
            self.simulator.start()
            self.current_robot = robot_name
            return {
                "success": True,
                "robot": robot_name,
                "info": self.simulator.get_model_info()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_simulation(self):
        """Stop current simulation."""
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
            self.current_robot = None

    def get_state(self) -> Optional[Dict]:
        """Get current simulation state."""
        if not self.simulator:
            return None

        state = self.simulator.get_state()
        return {
            "timestamp": state.timestamp,
            "qpos": state.qpos.tolist(),
            "qvel": state.qvel.tolist(),
            "joint_pos": state.joint_pos.tolist(),
            "joint_vel": state.joint_vel.tolist(),
            "joint_tau": state.joint_tau.tolist(),
            "imu_quat": state.imu_quat.tolist(),
            "imu_gyro": state.imu_gyro.tolist(),
            "imu_acc": state.imu_acc.tolist(),
            "foot_pos": state.foot_pos.tolist(),
        }

    def set_control(self, ctrl: list[float]):
        """Set motor control."""
        if self.simulator:
            self.simulator.set_control(np.array(ctrl))

    def reset(self):
        """Reset simulation."""
        if self.simulator:
            self.simulator.reset()

    async def register_websocket(self, websocket: WebSocket):
        """Register a new WebSocket connection."""
        await websocket.accept()
        self.websockets.append(websocket)

    def unregister_websocket(self, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        if websocket in self.websockets:
            self.websockets.remove(websocket)

    async def broadcast_state(self):
        """Broadcast simulation state to all connected clients."""
        while True:
            if self.websockets and self.simulator:
                state = self.get_state()
                if state:
                    message = json.dumps({"type": "state", "data": state})
                    disconnected = []
                    for ws in self.websockets:
                        try:
                            await ws.send_text(message)
                        except Exception:
                            disconnected.append(ws)
                    for ws in disconnected:
                        self.unregister_websocket(ws)
            await asyncio.sleep(1 / 30)  # 30 Hz broadcast


# Global simulation manager
manager = SimulationManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Store event loop for later use
    manager.loop = asyncio.get_event_loop()

    # Start state broadcast task
    manager.state_broadcast_task = asyncio.create_task(manager.broadcast_state())

    # Auto-start default simulation
    manager.start_simulation(SIM_CONFIG.default_robot)

    yield

    # Cleanup
    if manager.state_broadcast_task:
        manager.state_broadcast_task.cancel()
    manager.stop_simulation()


# Create FastAPI app
app = FastAPI(
    title="MuJoCo Robot Simulator",
    description="Web interface for Go2/G1 MuJoCo simulation",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve main page."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return FileResponse(str(template_path))
    return HTMLResponse("<h1>MuJoCo Simulator</h1><p>Templates not found</p>")


@app.get("/api/robots")
async def list_robots():
    """List available robots."""
    return {
        "robots": list(ROBOTS.keys()),
        "current": manager.current_robot,
    }


@app.post("/api/simulation/start/{robot_name}")
async def start_simulation(robot_name: str):
    """Start simulation with specified robot."""
    result = manager.start_simulation(robot_name)
    return result


@app.post("/api/simulation/stop")
async def stop_simulation():
    """Stop current simulation."""
    manager.stop_simulation()
    return {"success": True}


@app.post("/api/simulation/reset")
async def reset_simulation():
    """Reset simulation to initial state."""
    manager.reset()
    return {"success": True}


@app.get("/api/simulation/state")
async def get_state():
    """Get current simulation state."""
    state = manager.get_state()
    if state:
        return {"success": True, "state": state}
    return {"success": False, "error": "No simulation running"}


@app.get("/api/simulation/info")
async def get_info():
    """Get simulation information."""
    if manager.simulator:
        return {"success": True, "info": manager.simulator.get_model_info()}
    return {"success": False, "error": "No simulation running"}


@app.post("/api/control")
async def set_control(ctrl: list[float]):
    """Set motor control commands."""
    manager.set_control(ctrl)
    return {"success": True}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await manager.register_websocket(websocket)
    try:
        while True:
            # Receive commands from client
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "control":
                manager.set_control(msg.get("ctrl", []))
            elif msg.get("type") == "reset":
                manager.reset()
            elif msg.get("type") == "switch_robot":
                robot_name = msg.get("robot", "go2")
                result = manager.start_simulation(robot_name)
                await websocket.send_text(json.dumps({"type": "switch_result", "data": result}))

    except WebSocketDisconnect:
        manager.unregister_websocket(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.unregister_websocket(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SIM_CONFIG.web_port)
