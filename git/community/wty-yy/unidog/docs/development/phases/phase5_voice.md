# 阶段五: 语音 + MCP 控制

**预计时间**: 1 周  
**目标**: 实现自然语言语音控制机器狗, 通过 MCP 协议连接 LLM

---

## 里程碑

- [ ] Whisper STT 语音识别集成
- [ ] MCP Server 开发完成
- [ ] LLM API 集成 (Claude/GPT-4o)
- [ ] 自然语言命令解析
- [ ] "STOP" 紧急停止功能
- [ ] 端到端语音控制测试

---

## 详细步骤

### Step 5.1: 安装语音依赖

```bash
# 安装 Whisper (C++ 版本, 更高效)
pip3 install faster-whisper

# 或使用 Python 版本
pip3 install openai-whisper

# 安装麦克风库
pip3 install pyaudio sounddevice
```

### Step 5.2: 创建 MCP Server

创建文件: `~/git/community/unidog_ws/mcp_server/server.py`

```python
#!/usr/bin/env python3
"""
UniDog MCP Server
连接 LLM 和机器狗控制接口
"""

import json
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel

# MCP Server 实例
server = Server("unidog-mcp")

# 工具定义
TOOLS = [
    Tool(
        name="navigate_to",
        description="让机器狗自主导航到指定坐标点",
        inputSchema={
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "X 坐标 (米)"},
                "y": {"type": "number", "description": "Y 坐标 (米)"},
                "yaw": {"type": "number", "description": "目标朝向 (弧度)", "default": 0}
            },
            "required": ["x", "y"]
        }
    ),
    Tool(
        name="set_velocity",
        description="直接设置机器狗的移动速度",
        inputSchema={
            "type": "object",
            "properties": {
                "vx": {"type": "number", "description": "前进速度 (m/s)"},
                "vy": {"type": "number", "description": "侧向速度 (m/s)"},
                "omega": {"type": "number", "description": "转向角速度 (rad/s)"}
            },
            "required": ["vx", "omega"]
        }
    ),
    Tool(
        name="get_robot_state",
        description="获取机器狗当前状态",
    ),
    Tool(
        name="trigger_action",
        description="触发预设动作",
        inputSchema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["stand_up", "sit_down", "jump", "stop"]
                }
            },
            "required": ["action"]
        }
    ),
    Tool(
        name="emergency_stop",
        description="紧急停止机器狗 (最高优先级)"
    )
]

# 工具实现
async def call_navigate_to(x: float, y: float, yaw: float = 0) -> str:
    # 调用 Nav2 Action
    # ...
    return f"已发送导航目标: ({x}, {y})"

async def call_set_velocity(vx: float, vy: float, omega: float) -> str:
    # 发送到 WebSocket Bridge
    # ...
    return f"速度已设置: vx={vx}, vy={vy}, omega={omega}"

async def call_get_robot_state() -> dict:
    # 从 WebSocket Bridge 获取状态
    # ...
    return {
        "battery": 85,
        "position": {"x": 1.2, "y": -0.5, "z": 0.0},
        "velocity": {"vx": 0.0, "vy": 0.0, "omega": 0.0},
        "status": "standing"
    }

async def call_trigger_action(action: str) -> str:
    # 触发动作
    # ...
    return f"已执行动作: {action}"

async def call_emergency_stop() -> str:
    # 紧急停止 - 最高优先级
    # 绕过所有层级, 直接发零速度
    # ...
    return "紧急停止已执行"

@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> TextContent:
    if name == "navigate_to":
        result = await call_navigate_to(
            arguments["x"], arguments["y"], arguments.get("yaw", 0)
        )
    elif name == "set_velocity":
        result = await call_set_velocity(
            arguments["vx"], arguments["vy"], arguments["omega"]
        )
    elif name == "get_robot_state":
        result = await call_get_robot_state()
    elif name == "trigger_action":
        result = await call_trigger_action(arguments["action"])
    elif name == "emergency_stop":
        result = await call_emergency_stop()
    else:
        result = f"Unknown tool: {name}"
    
    return TextContent(type="text", text=str(result))

# System Prompt
SYSTEM_PROMPT = """
你是一个机器狗控制助手, 名字叫小GO。
你可以控制 Unitree Go2 四足机器人。

已知位置:
- A点: (5.2, -1.3) # 实验室入口
- B点: (10.0, 0.0) # 服务器机房
- 充电桩: (0.0, 0.0)

安全规则:
1. 任何情况下, "STOP" 或 "停止" 指令必须立即执行 emergency_stop()
2. 不要让机器狗撞向障碍物
3. 电量低于 20% 时提醒用户
"""

async def main():
    # 启动 MCP Server
    # 等待 LLM 连接
    async with server.run_transport("stdio"):
        await server.wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 5.3: 创建语音客户端

创建文件: `~/git/community/unidog_ws/mcp_server/voice_client.py`

```python
#!/usr/bin/env python3
"""
UniDog Voice Client
麦克风 → Whisper STT → LLM → MCP Server
"""

import pyaudio
import numpy as np
from faster_whisper import WhisperModel
import websocket
import json
import openai

# 配置
OPENAI_API_KEY = "your-api-key"  # 或使用 Claude API
WHISPER_MODEL = "base"  # tiny/base/small/medium/large

class VoiceClient:
    def __init__(self):
        # 加载 Whisper
        self.model = WhisperModel(WHISPER_MODEL, device="cpu")
        
        # 麦克风
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.pyaudio = pyaudio.PyAudio()
        
        # LLM Client
        self.llm_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # WebSocket (连接 MCP Server)
        # 或使用 stdio 直接调用 MCP Server
        
    def listen(self):
        """监听麦克风, 检测语音"""
        stream = self.pyaudio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        frames = []
        silence_count = 0
        is_recording = False
        silence_threshold = 30  # 静音帧数阈值
        
        while True:
            data = stream.read(self.CHUNK)
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.abs(audio_data).mean()
            
            # 检测语音开始/结束
            if amplitude > 500 and not is_recording:
                is_recording = True
                frames = []
            
            if is_recording:
                frames.append(data)
                
                if amplitude < 500:
                    silence_count += 1
                    if silence_count > silence_threshold:
                        # 语音结束, 处理
                        self.process_audio(frames)
                        frames = []
                        is_recording = False
                        silence_count = 0
                else:
                    silence_count = 0
    
    def process_audio(self, frames):
        """将音频转为文字, 发送给 LLM"""
        import io
        import wave
        
        # 保存为 WAV
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.pyaudio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
        
        buffer.seek(0)
        
        # Whisper 识别
        segments, _ = self.model.transcribe(buffer, language="zh")
        text = "".join([s.text for s in segments])
        
        if text.strip():
            print(f"识别: {text}")
            self.send_to_llm(text)
    
    def send_to_llm(self, text: str):
        """发送给 LLM, 获取响应"""
        response = self.llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ]
        )
        
        reply = response.choices[0].message.content
        print(f"LLM 回复: {reply}")

if __name__ == "__main__":
    client = VoiceClient()
    client.listen()
```

### Step 5.4: 安全机制

```python
# 紧急停止 - 最高优先级
async def check_for_emergency(text: str) -> bool:
    emergency_keywords = ["stop", "停止", "停下", "emergency", "救命", "危险"]
    return any(kw in text.lower() for kw in emergency_keywords)

# 在 voice_client.py 中
def process_audio(self, frames):
    audio_bytes = b''.join(frames)
    # ... Whisper 识别 ...
    
    if self.check_for_emergency(text):
        # 绕过 LLM, 直接调用 emergency_stop
        self.emergency_stop()
        return
    
    self.send_to_llm(text)
```

### Step 5.5: 端到端测试

```bash
# 终端 1: 启动 MCP Server
cd ~/git/community/unidog_ws/mcp_server
python3 server.py

# 终端 2: 启动语音客户端
python3 voice_client.py

# 对着麦克风说:
# "小GO, 去A点巡检一下"
# "STOP" (测试紧急停止)
```

---

## 验收标准

| 检查项 | 预期结果 | 验证方法 |
|--------|---------|---------|
| 麦克风识别 | 语音转为文字 | 终端输出 |
| LLM 理解 | 正确解析意图 | 终端输出 |
| MCP 调用 | 执行对应工具 | 终端输出 |
| 狗响应 | 按指令移动 | 眼睛观察 |
| 紧急停止 | 说 STOP 后立即停止 | 实际测试 |

---

## 全部阶段完成!

→ [真机部署指南](../deployment.md)
