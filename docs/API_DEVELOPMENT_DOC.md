# Unitree WebRTC Connect API 开发文档

> 基于 `unitree_webrtc_connect` v2.0.4 — Python WebRTC 驱动，支持 Unitree Go2 和 G1 机器人

---

## 目录

- [1. 支持的固件版本](#1-支持的固件版本)
- [2. 快速上手](#2-快速上手)
  - [2.1 安装](#21-安装)
  - [2.2 连接方式](#22-连接方式)
- [3. 通用 API（Go2 + G1）](#3-通用-apigo2--g1)
  - [3.1 连接 API (UnitreeWebRTCConnection)](#31-连接-api-unitreewebrtcconnection)
  - [3.2 数据通道 Pub/Sub 核心](#32-数据通道-pubsub-核心)
  - [3.3 运控切换服务 (MOTION_SWITCHER)](#33-运控切换服务-motion_switcher)
  - [3.4 高层运动服务 (SPORT_MOD)](#34-高层运动服务-sport_mod)
  - [3.5 AI 运动服务](#35-ai-运动服务)
  - [3.6 音量灯光服务 (VUI)](#36-音量灯光服务-vui)
  - [3.7 设备状态服务](#37-设备状态服务)
  - [3.8 避障服务 (OBSTACLES_AVOID)](#38-避障服务-obstacles_avoid)
  - [3.9 虚拟手柄控制](#39-虚拟手柄控制)
- [4. Go2 专属 API](#4-go2-专属-api)
  - [4.1 音频服务](#41-音频服务)
  - [4.2 视频服务](#42-视频服务)
  - [4.3 LiDAR 服务](#43-lidar-服务)
  - [4.4 多播扫描器](#44-多播扫描器)
- [5. G1 专属 API](#5-g1-专属-api)
  - [5.1 机械臂服务](#51-机械臂服务)
  - [5.2 行走模式切换](#52-行走模式切换)
- [6. 常量速查表](#6-常量速查表)
  - [RTC_TOPIC](#rtc_topic)
  - [SPORT_CMD](#sport_cmd)
  - [VUI_COLOR](#vui_color)
  - [AUDIO_API](#audio_api)
  - [DATA_CHANNEL_TYPE](#data_channel_type)
- [7. 错误码参考](#7-错误码参考)
- [8. 完整示例代码集](#8-完整示例代码集)

---

## 1. 支持的固件版本

> **请在使用前确认您的机器人固件版本兼容性。**

| 机型 | 固件版本 | 备注 |
|------|----------|------|
| **Go2** | 1.1.x 系列: 1.1.1 – 1.1.11 | 最新可用 |
| **Go2** | 1.0.x 系列: 1.0.19 – 1.0.25 | |
| **G1** | 1.4.0 | 最新可用 |

支持机型: Go2 AIR / PRO / EDU, G1 AIR / EDU

---

## 2. 快速上手

### 2.1 安装

```bash
# 推荐方式 (pip)
sudo apt update
sudo apt install -y python3-pip portaudio19-dev
pip install unitree_webrtc_connect

# 手动安装
git clone https://github.com/legion1581/unitree_webrtc_connect.git
cd unitree_webrtc_connect
pip install -e .
```

### 2.2 连接方式

支持三种连接方式:

```python
import asyncio
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# 方式1: AP模式 — 直连机器人热点 (机器人IP固定为 192.168.12.1)
conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)

# 方式2: STA模式 — 局域网连接 (机器人和客户端在同一局域网)
conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.8.181")
# 或通过序列号自动发现IP
conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber="B42D2000XXXXXXXX")

# 方式3: 远程模式 — 通过Unitree TURN服务器远程连接
conn = UnitreeWebRTCConnection(
    WebRTCConnectionMethod.Remote,
    serialNumber="B42D2000XXXXXXXX",
    username="email@gmail.com",
    password="pass"
)

await conn.connect()
```

---

## 3. 通用 API（Go2 + G1）

### 3.1 连接 API (UnitreeWebRTCConnection)

`[通用]` Go2 + G1

#### 类定义

```python
UnitreeWebRTCConnection(connectionMethod, serialNumber=None, ip=None, username=None, password=None)
```

#### 构造参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `connectionMethod` | `WebRTCConnectionMethod` | 连接方式: `LocalAP`, `LocalSTA`, `Remote` |
| `serialNumber` | `str` | 机器人序列号 (Remote模式必填, LocalSTA可选) |
| `ip` | `str` | 机器人IP地址 (LocalSTA模式推荐) |
| `username` | `str` | Unitree账号邮箱 (Remote模式必填) |
| `password` | `str` | Unitree账号密码 (Remote模式必填) |

#### 方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `await conn.connect()` | `None` | 建立WebRTC连接 |
| `await conn.disconnect()` | `None` | 断开连接 |
| `await conn.reconnect()` | `None` | 先断开再重连 |

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `conn.isConnected` | `bool` | 是否已连接 |
| `conn.pc` | `RTCPeerConnection` | WebRTC对等连接对象 |
| `conn.datachannel` | `WebRTCDataChannel` | 数据通道对象 |
| `conn.audio` | `WebRTCAudioChannel` | 音频通道 (仅Go2) |
| `conn.video` | `WebRTCVideoChannel` | 视频通道 (仅Go2) |

#### 完整示例

```python
import asyncio
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.8.181")
    await conn.connect()
    print(f"已连接: {conn.isConnected}")
    # ... 使用API ...
    await conn.disconnect()

asyncio.run(main())
```

---

### 3.2 数据通道 Pub/Sub 核心

`[通用]` Go2 + G1

通过 `conn.datachannel.pub_sub` 访问发布/订阅功能。

#### publish_request_new

发送服务请求并等待响应（用于绝大多数服务调用）。

```python
response = await pub_sub.publish_request_new(topic, options)
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `topic` | `str` | 是 | 服务主题，如 `RTCTOPIC["SPORTMOD"]` |
| `options` | `dict` | 是 | 请求选项 |
| `options["api_id"]` | `int` | 是 | API ID，如 `SPORTCMD["Hello"]` |
| `options["parameter"]` | `dict/str` | 否 | 请求参数 |
| `options["id"]` | `int` | 否 | 自定义请求ID |
| `options["priority"]` | `int` | 否 | 优先级 |

**返回值**: `dict` — 服务响应消息

#### subscribe

订阅主题数据（用于实时数据接收）。

```python
pub_sub.subscribe(topic, callback)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `topic` | `str` | 主题名称 |
| `callback` | `function(message)` | 回调函数, message包含 `type`, `topic`, `data` |

#### publish_without_callback

发送消息但不等待响应（用于虚拟手柄等持续发送场景）。

```python
pub_sub.publish_without_callback(topic, data, msg_type=None)
```

#### unsubscribe

取消订阅。

```python
pub_sub.unsubscribe(topic)
```

---

### 3.3 运控切换服务 (MOTION_SWITCHER)

`[通用]` Go2 + G1

对应官方 SDK 05-06 运控切换服务接口

**Topic**: `rt/api/motion_switcher/request`

在执行运动命令前，需先确认当前运动模式。`normal` 模式用于高层运动和AI运动，`ai` 模式用于特殊动作（倒立等）。

| api_id | 功能 | 参数 | 说明 |
|--------|------|------|------|
| 1001 | 查询当前模式 | 无 | 返回 `{"name": "normal"}` 或 `{"name": "ai"}` |
| 1002 | 切换模式 | `{"name": "normal"}` 或 `{"name": "ai"}` | 切换后需等待几秒 |

#### 代码示例

```python
import json
from unitree_webrtc_connect.constants import RTC_TOPIC

# 查询当前模式
response = await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["MOTION_SWITCHER"],
    {"api_id": 1001}
)
if response['data']['header']['status']['code'] == 0:
    data = json.loads(response['data']['data'])
    current_mode = data['name']
    print(f"当前模式: {current_mode}")

# 切换到 normal 模式
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["MOTION_SWITCHER"],
    {"api_id": 1002, "parameter": {"name": "normal"}}
)
await asyncio.sleep(5)  # 等待切换完成

# 切换到 ai 模式
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["MOTION_SWITCHER"],
    {"api_id": 1002, "parameter": {"name": "ai"}}
)
await asyncio.sleep(10)  # ai模式切换需要更长时间
```

---

### 3.4 高层运动服务 (SPORT_MOD)

`[通用]` Go2 + G1

对应官方 SDK 05-07 高层运动服务接口

**Topic**: `rt/api/sport/request`

所有运动命令通过 `publish_request_new` 发送。大部分命令无需参数，`Move` 命令需要坐标参数。

#### 基础动作

| 命令 | api_id | 参数 | 说明 |
|------|--------|------|------|
| Damp | 1001 | 无 | 阻尼模式（软关闭） |
| BalanceStand | 1002 | 无 | 平衡站立 |
| StopMove | 1003 | 无 | 停止当前移动 |
| StandUp | 1004 | 无 | 站起 |
| StandDown | 1005 | 无 | 趴下 |
| RecoveryStand | 1006 | 无 | 恢复站立（异常恢复） |
| Sit | 1009 | 无 | 坐下 |
| RiseSit | 1010 | 无 | 从坐姿站起 |

#### 移动控制

| 命令 | api_id | 参数 | 说明 |
|------|--------|------|------|
| **Move** | 1008 | `{"x": float, "y": float, "z": float}` | **持续移动** — x:前后(正=前), y:左右(正=左), z:旋转(正=逆时针) |

> **Move 参数范围**: x 约 -1.0 ~ 1.0, y 约 -1.0 ~ 1.0, z 约 -1.0 ~ 1.0。实际速度与 SpeedLevel 相关。

#### 参数调整

| 命令 | api_id | 参数 | 说明 |
|------|--------|------|------|
| BodyHeight | 1013 | `{"data": float}` | 设置身体高度 |
| FootRaiseHeight | 1014 | `{"data": float}` | 设置抬脚高度 |
| SpeedLevel | 1015 | `{"data": int}` | 设置速度等级 |
| SwitchGait | 1011 | `{"data": int}` | 切换步态 |
| ContinuousGait | 1019 | 无 | 连续步态 |

#### 查询

| 命令 | api_id | 说明 |
|------|--------|------|
| GetBodyHeight | 1024 | 获取当前身体高度 |
| GetFootRaiseHeight | 1025 | 获取当前抬脚高度 |
| GetSpeedLevel | 1026 | 获取当前速度等级 |
| GetState | 1034 | 获取运动状态 |

#### 特技动作

| 命令 | api_id | 参数 | 说明 |
|------|--------|------|------|
| Hello | 1016 | 无 | 招手 |
| Stretch | 1017 | 无 | 伸展 |
| Dance1 | 1022 | 无 | 跳舞1 |
| Dance2 | 1023 | 无 | 跳舞2 |
| Wallow | 1021 | 无 | 打滚 |
| Content | 1020 | 无 | 满足动作 |
| WiggleHips | 1033 | 无 | 扭屁股 |
| Scrape | 1029 | 无 | 刮地 |
| FingerHeart | 1036 | 无 | 比心 |
| FrontJump | 1031 | 无 | 前跳 |
| FrontPounce | 1032 | 无 | 前扑 |
| FrontFlip | 1030 | `{"data": True}` | 前空翻 |
| BackFlip | 1044 | `{"data": True}` | 后空翻 |
| LeftFlip | 1042 | `{"data": True}` | 左空翻 |
| RightFlip | 1043 | `{"data": True}` | 右空翻 |
| FreeWalk | 1045 | 无 | 自由行走 |
| LeadFollow | 1045 | 无 | 跟随 |
| Standup | 1050 | 无 | 站立 |
| CrossWalk | 1051 | 无 | 交叉行走 |
| EconomicGait | 1035 | 无 | 经济步态 |
| Pose | 1028 | 无 | 姿势调整 |

#### 代码示例

```python
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

# 招手
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["Hello"]}
)

# 前进 (x=0.5m/s)
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["Move"], "parameter": {"x": 0.5, "y": 0, "z": 0}}
)

# 后退
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["Move"], "parameter": {"x": -0.5, "y": 0, "z": 0}}
)

# 左移
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["Move"], "parameter": {"x": 0, "y": 0.3, "z": 0}}
)

# 旋转 (逆时针)
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["Move"], "parameter": {"x": 0, "y": 0, "z": 0.5}}
)

# 停止移动
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["StopMove"]}
)

# 站起
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["StandUp"]}
)

# 跳舞
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["Dance1"]}
)

# 前空翻
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["FrontFlip"], "parameter": {"data": True}}
)
```

---

### 3.5 AI 运动服务

`[通用]` Go2 + G1

对应官方 SDK 05-08 AI 运动服务接口

AI 运动需要先切换到 `ai` 模式，再发送运动命令。

#### 步骤

1. 使用 MOTION_SWITCHER 切换到 `ai` 模式
2. 等待切换完成（约10秒）
3. 发送AI运动命令
4. 完成后可切换回 `normal` 模式

#### AI 模式专属命令

| 命令 | api_id | 参数 | 说明 |
|------|--------|------|------|
| StandOut | 1039 | `{"data": True/False}` | AI模式切换动作状态(True=进入, False=退出) |
| Handstand | 1301 | 无 | 倒立 |
| CrossStep | 1302 | 无 | 交叉步 |
| OnesidedStep | 1303 | 无 | 单侧步 |
| Bound | 1304 | 无 | 弹跳 |
| MoonWalk | 1305 | 无 | 太空步 |

#### 代码示例

```python
# 1. 切换到 ai 模式
print("切换到AI模式...")
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["MOTION_SWITCHER"],
    {"api_id": 1002, "parameter": {"name": "ai"}}
)
await asyncio.sleep(10)

# 2. 进入倒立
print("进入倒立...")
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["StandOut"], "parameter": {"data": True}}
)
await asyncio.sleep(5)

# 3. 退出倒立
print("退出倒立...")
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["SPORT_MOD"],
    {"api_id": SPORT_CMD["StandOut"], "parameter": {"data": False}}
)

# 4. 切回 normal 模式
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["MOTION_SWITCHER"],
    {"api_id": 1002, "parameter": {"name": "normal"}}
)
```

---

### 3.6 音量灯光服务 (VUI)

`[通用]` Go2 + G1

对应官方 SDK 05-04 音量灯光服务接口

**Topic**: `rt/api/vui/request`

#### API 列表

| api_id | 功能 | 参数 | 说明 |
|--------|------|------|------|
| 1003 | 设置音量 | `{"volume": 0-10}` | 0=静音, 10=最大 |
| 1004 | 获取音量 | 无 | 返回 `{"volume": int}` |
| 1005 | 设置亮度 | `{"brightness": 0-10}` | 0=灭, 10=最亮 |
| 1006 | 获取亮度 | 无 | 返回 `{"brightness": int}` |
| 1007 | 设置LED颜色 | `{"color": str, "time": int, "flash_cycle": int}` | `time`=持续秒数, `flash_cycle`=闪烁周期ms(可选, 499~time*1000) |

#### VUI_COLOR 颜色常量

| 常量 | 值 | 说明 |
|------|----|------|
| `VUI_COLOR.WHITE` | `"white"` | 白色 |
| `VUI_COLOR.RED` | `"red"` | 红色 |
| `VUI_COLOR.YELLOW` | `"yellow"` | 黄色 |
| `VUI_COLOR.BLUE` | `"blue"` | 蓝色 |
| `VUI_COLOR.GREEN` | `"green"` | 绿色 |
| `VUI_COLOR.CYAN` | `"cyan"` | 青色 |
| `VUI_COLOR.PURPLE` | `"purple"` | 紫色 |

#### 代码示例

```python
from unitree_webrtc_connect.constants import RTC_TOPIC, VUI_COLOR

# 设置音量为5 (50%)
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["VUI"],
    {"api_id": 1003, "parameter": {"volume": 5}}
)

# 获取当前音量
response = await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["VUI"],
    {"api_id": 1004}
)
if response['data']['header']['status']['code'] == 0:
    data = json.loads(response['data']['data'])
    print(f"当前音量: {data['volume']}/10")

# 设置亮度从0到10逐步增加
for brightness in range(0, 11):
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["VUI"],
        {"api_id": 1005, "parameter": {"brightness": brightness}}
    )
    await asyncio.sleep(0.5)

# LED紫色常亮5秒
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["VUI"],
    {"api_id": 1007, "parameter": {"color": VUI_COLOR.PURPLE, "time": 5}}
)

# LED青色闪烁5秒 (每秒闪一次)
await conn.datachannel.pub_sub.publish_request_new(
    RTC_TOPIC["VUI"],
    {"api_id": 1007, "parameter": {"color": VUI_COLOR.CYAN, "time": 5, "flash_cycle": 1000}}
)
```

---

### 3.7 设备状态服务

`[通用]` Go2 + G1

对应官方 SDK 05-05 设备状态服务接口

通过订阅 Topic 实时获取机器人状态数据。

#### 低级状态 (LOW_STATE)

**Topic**: `rt/lf/lowstate`

| 字段 | 类型 | 说明 |
|------|------|------|
| `imu_state` | `dict` | IMU状态: `rpy`, `quaternion`, `gyroscope`, `accelerometer`, `temperature` |
| `motor_state` | `list[12]` | 12个电机状态: `q`(角度), `temperature`, `lost` |
| `bms_state` | `dict` | 电池管理: `soc`(电量%), `current`(mA), `cycle`, `version_high/low`, `bq_ntc`, `mcu_ntc` |
| `foot_force` | `list` | 四足力传感器数据 |
| `temperature_ntc1` | `float` | NTC温度 |
| `power_v` | `float` | 电源电压 |

#### 多重状态 (MULTIPLE_STATE)

**Topic**: `rt/multiplestate`

| 字段 | 类型 | 说明 |
|------|------|------|
| `bodyHeight` | `float` | 身体高度 (米) |
| `brightness` | `int` | 亮度等级 |
| `footRaiseHeight` | `float` | 抬脚高度 (米) |
| `obstaclesAvoidSwitch` | `bool` | 避障开关状态 |
| `speedLevel` | `int` | 速度等级 |
| `uwbSwitch` | `bool` | UWB开关状态 |
| `volume` | `int` | 音量等级 |

#### 运动模式状态 (LF_SPORT_MOD_STATE)

**Topic**: `rt/lf/sportmodestate`

| 字段 | 类型 | 说明 |
|------|------|------|
| `mode` | `int` | 当前模式 |
| `progress` | `float` | 动作进度 |
| `gait_type` | `int` | 步态类型 |
| `foot_raise_height` | `float` | 抬脚高度 |
| `position` | `list` | 位置 [x, y, z] |
| `body_height` | `float` | 身体高度 |
| `velocity` | `list` | 速度 [vx, vy, vz] |
| `yaw_speed` | `float` | 偏航速度 |
| `range_obstacle` | `float` | 障碍物距离 |
| `foot_force` | `list` | 足力 |
| `foot_position_body` | `list` | 足相对身体位置 |
| `foot_speed_body` | `list` | 足相对身体速度 |
| `imu_state` | `dict` | IMU状态 |

#### 代码示例

```python
# 订阅低级状态
def lowstate_callback(message):
    data = message['data']
    imu = data['imu_state']['rpy']
    print(f"姿态: Roll={imu[0]:.2f}, Pitch={imu[1]:.2f}, Yaw={imu[2]:.2f}")
    print(f"电池: {data['bms_state']['soc']}%")

conn.datachannel.pub_sub.subscribe(RTC_TOPIC['LOW_STATE'], lowstate_callback)

# 订阅多重状态
def multiplestate_callback(message):
    data = json.loads(message['data'])
    print(f"身体高度: {data['bodyHeight']:.2f}m")
    print(f"避障: {'开' if data['obstaclesAvoidSwitch'] else '关'}")

conn.datachannel.pub_sub.subscribe(RTC_TOPIC['MULTIPLE_STATE'], multiplestate_callback)

# 订阅运动模式状态
def sportmodestate_callback(message):
    data = message['data']
    print(f"模式: {data['mode']}, 步态: {data['gait_type']}")
    print(f"位置: {data['position']}, 速度: {data['velocity']}")

conn.datachannel.pub_sub.subscribe(RTC_TOPIC['LF_SPORT_MOD_STATE'], sportmodestate_callback)
```

---

### 3.8 避障服务 (OBSTACLES_AVOID)

`[通用]` Go2 + G1

对应官方 SDK 05-03 避障服务接口

**Topic**: `rt/api/obstacles_avoid/request`

避障开关状态通过 MULTIPLE_STATE 的 `obstaclesAvoidSwitch` 字段查看。

```python
# 订阅多重状态查看避障开关
def callback(message):
    data = json.loads(message['data'])
    avoid_on = data['obstaclesAvoidSwitch']
    print(f"避障: {'开启' if avoid_on else '关闭'}")

conn.datachannel.pub_sub.subscribe(RTC_TOPIC['MULTIPLE_STATE'], callback)
```

---

### 3.9 虚拟手柄控制

`[通用]` Go2 + G1

**Topic**: `rt/wirelesscontroller`

通过持续发送手柄数据实现移动/转向控制，无需等待响应。

#### 参数说明

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `lx` | `float` | -1.0 ~ 1.0 | 左摇杆X轴 |
| `ly` | `float` | -1.0 ~ 1.0 | 左摇杆Y轴 (前后控制, 正=前) |
| `rx` | `float` | -1.0 ~ 1.0 | 右摇杆X轴 (旋转控制, 正=逆时针) |
| `ry` | `float` | -1.0 ~ 1.0 | 右摇杆Y轴 |
| `keys` | `int` | - | 按键状态, 默认0 |

#### 代码示例

```python
# 前进
conn.datachannel.pub_sub.publish_without_callback(
    "rt/wirelesscontroller",
    {"lx": 0.0, "ly": 0.5, "rx": 0.0, "ry": 0.0, "keys": 0}
)
await asyncio.sleep(3)

# 旋转 (逆时针)
conn.datachannel.pub_sub.publish_without_callback(
    "rt/wirelesscontroller",
    {"lx": 0.0, "ly": 0.0, "rx": 1.0, "ry": 0.0, "keys": 0}
)
await asyncio.sleep(3)

# 停止
conn.datachannel.pub_sub.publish_without_callback(
    "rt/wirelesscontroller",
    {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "keys": 0}
)
```

---

## 4. Go2 专属 API

### 4.1 音频服务

`[仅 Go2]`

对应官方 SDK 05-11 多媒体服务接口

#### 基础音频通道 (WebRTCAudioChannel)

通过 `conn.audio` 访问。

| 方法 | 说明 |
|------|------|
| `conn.audio.switchAudioChannel(True/False)` | 开启/关闭音频通道 |
| `conn.audio.add_track_callback(callback)` | 添加音频帧回调 |

回调函数签名: `async def callback(frame)` — frame 为 aiortc MediaStreamTrack 帧

```python
import numpy as np

async def audio_callback(frame):
    audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
    # 处理音频数据 (48kHz, 立体声, 16-bit PCM)

conn.audio.switchAudioChannel(True)
conn.audio.add_track_callback(audio_callback)
```

#### AudioHub 音频管理 (WebRTCAudioHub)

提供完整的音频文件管理功能。

```python
from unitree_webrtc_connect.webrtc_audiohub import WebRTCAudioHub

audio_hub = WebRTCAudioHub(conn, logger)
```

| 方法 | 参数 | 说明 |
|------|------|------|
| `await audio_hub.get_audio_list()` | 无 | 获取音频文件列表 |
| `await audio_hub.play_by_uuid(uuid)` | `uuid: str` | 按UUID播放音频 |
| `await audio_hub.pause()` | 无 | 暂停播放 |
| `await audio_hub.resume()` | 无 | 恢复播放 |
| `await audio_hub.set_play_mode(mode)` | `mode: str` | 设置播放模式: `single_cycle`, `no_cycle`, `list_loop` |
| `await audio_hub.get_play_mode()` | 无 | 获取当前播放模式 |
| `await audio_hub.rename_record(uuid, new_name)` | `uuid: str, new_name: str` | 重命名音频 |
| `await audio_hub.delete_record(uuid)` | `uuid: str` | 删除音频 |
| `await audio_hub.upload_audio_file(path)` | `path: str` | 上传音频文件 (MP3/WAV, 自动分块) |
| `await audio_hub.enter_megaphone()` | 无 | 进入扩音器模式 |
| `await audio_hub.exit_megaphone()` | 无 | 退出扩音器模式 |
| `await audio_hub.upload_megaphone(path)` | `path: str` | 上传扩音器音频 |

#### 发送音频到机器人扬声器

```python
from aiortc.contrib.media import MediaPlayer

# 播放本地MP3文件
player = MediaPlayer("audio.mp3")
conn.pc.addTrack(player.audio)

# 播放网络电台
player = MediaPlayer("https://nashe1.hostingradio.ru:80/ultra-128.mp3")
conn.pc.addTrack(player.audio)
```

---

### 4.2 视频服务

`[仅 Go2]`

通过 `conn.video` 访问。

| 方法 | 说明 |
|------|------|
| `conn.video.switchVideoChannel(True/False)` | 开启/关闭视频通道 |
| `conn.video.add_track_callback(callback)` | 添加视频帧回调 |

回调函数签名: `async def callback(track)` — track 为 aiortc MediaStreamTrack

```python
import cv2
import numpy as np

async def video_callback(track):
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")
        cv2.imshow('Go2 Camera', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

conn.video.switchVideoChannel(True)
conn.video.add_track_callback(video_callback)
```

---

### 4.3 LiDAR 服务

`[仅 Go2]`

对应官方 SDK 05-10 LiDAR 服务接口

#### 步骤

1. 禁用流量节省
2. 设置解码器
3. 开启LiDAR
4. 订阅点云数据

#### 方法

| 方法/操作 | 说明 |
|-----------|------|
| `await conn.datachannel.disableTrafficSaving(True)` | 禁用流量节省 (订阅LiDAR前必须) |
| `conn.datachannel.set_decoder("libvoxel")` | 使用libvoxel解码器 (默认, 需要wasmtime) |
| `conn.datachannel.set_decoder("native")` | 使用原生解码器 (需要lz4) |
| `publish_without_callback("rt/utlidar/switch", "on")` | 开启LiDAR |
| `subscribe("rt/utlidar/voxel_map_compressed", callback)` | 订阅压缩点云 |

#### 解码器输出格式

**libvoxel 解码器**:
```python
{
    "point_count": int,
    "face_count": int,
    "positions": numpy.ndarray,  # uint8
    "uvs": numpy.ndarray,        # uint8
    "indices": numpy.ndarray     # uint32
}
```

**native 解码器**:
```python
{
    "points": numpy.ndarray  # shape (N, 3), float64
}
```

#### 代码示例

```python
# 1. 禁用流量节省
await conn.datachannel.disableTrafficSaving(True)

# 2. 设置解码器
conn.datachannel.set_decoder('libvoxel')

# 3. 开启LiDAR
conn.datachannel.pub_sub.publish_without_callback("rt/utlidar/switch", "on")

# 4. 订阅点云
def lidar_callback(message):
    data = message["data"]["data"]
    print(f"点数: {data['point_count']}")

conn.datachannel.pub_sub.subscribe("rt/utlidar/voxel_map_compressed", lidar_callback)
```

---

### 4.4 多播扫描器

`[仅 Go2]`

在局域网内自动发现 Go2 设备。

```python
from unitree_webrtc_connect.multicast_scanner import discover_ip_sn

# 扫描局域网设备 (默认超时2秒)
serial_to_ip = discover_ip_sn(timeout=2)

# 返回: {"B42D2000XXXXXXXX": "192.168.8.181", ...}

for sn, ip in serial_to_ip.items():
    print(f"序列号: {sn}, IP: {ip}")
```

---

## 5. G1 专属 API

### 5.1 机械臂服务

`[仅 G1]`

对应官方 SDK 05-17 D1 机械臂服务接口

**Topic**: `rt/api/arm/request`, api_id = **7106**

#### 动作列表

| action_id | 动作名称 | 说明 |
|-----------|----------|------|
| 12 | 左飞吻 | Left Kiss |
| 15 | 双手举 | Hands Up |
| 17 | 鼓掌 | Clap |
| 18 | 击掌 | High Five |
| 19 | 拥抱 | Hug |
| 20 | 左比心 | Arm Heart (Left) |
| 21 | 右比心 | Right Heart |
| 22 | 拒绝 | Reject |
| 23 | 右手举 | Right Hand Up |
| 24 | X光手势 | X-Ray |
| 25 | 面前挥手 | Face Wave |
| 26 | 挥手 | High Wave |
| 27 | 握手 | Handshake |
| 99 | 取消动作 | 收回手臂 |

#### 代码示例

```python
# 握手
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/arm/request",
    {"api_id": 7106, "parameter": {"data": 27}}
)
await asyncio.sleep(5)

# 击掌
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/arm/request",
    {"api_id": 7106, "parameter": {"data": 18}}
)
await asyncio.sleep(5)

# 拥抱
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/arm/request",
    {"api_id": 7106, "parameter": {"data": 19}}
)
await asyncio.sleep(5)

# 取消任何动作，收回手臂
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/arm/request",
    {"api_id": 7106, "parameter": {"data": 99}}
)
```

---

### 5.2 行走模式切换

`[仅 G1]`

**Topic**: `rt/api/sport/request`, api_id = **7101**

| data 值 | 模式 | 说明 |
|---------|------|------|
| 500 | Walk | 行走模式 |
| 501 | Walk (Control Waist) | 行走（腰部控制） |
| 801 | Run | 跑步模式 |

#### 代码示例

```python
# 切换到行走模式
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/sport/request",
    {"api_id": 7101, "parameter": {"data": 500}}
)
await asyncio.sleep(5)

# 切换到跑步模式
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/sport/request",
    {"api_id": 7101, "parameter": {"data": 801}}
)
await asyncio.sleep(5)

# 使用虚拟手柄移动
conn.datachannel.pub_sub.publish_without_callback(
    "rt/wirelesscontroller",
    {"lx": 0.0, "ly": 0.0, "rx": 1.0, "ry": 0.0, "keys": 0}
)
await asyncio.sleep(3)

# 停止
conn.datachannel.pub_sub.publish_without_callback(
    "rt/wirelesscontroller",
    {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "keys": 0}
)
```

---

## 6. 常量速查表

### RTC_TOPIC

| 常量 | Topic 值 | 说明 | 机型 |
|------|----------|------|------|
| `LOW_STATE` | `rt/lf/lowstate` | 低级状态 | 通用 |
| `MULTIPLE_STATE` | `rt/multiplestate` | 多重状态 | 通用 |
| `SPORT_MOD` | `rt/api/sport/request` | 运动服务 | 通用 |
| `SPORT_MOD_STATE` | `rt/sportmodestate` | 运动模式状态 | 通用 |
| `LF_SPORT_MOD_STATE` | `rt/lf/sportmodestate` | LF运动模式状态 | 通用 |
| `MOTION_SWITCHER` | `rt/api/motion_switcher/request` | 运控切换 | 通用 |
| `VUI` | `rt/api/vui/request` | 音量灯光 | 通用 |
| `OBSTACLES_AVOID` | `rt/api/obstacles_avoid/request` | 避障 | 通用 |
| `WIRELESS_CONTROLLER` | `rt/wirelesscontroller` | 虚拟手柄 | 通用 |
| `LOW_CMD` | `rt/lowcmd` | 底层命令 | 通用 |
| `ARM_COMMAND` | `rt/arm_Command` | 机械臂命令 | G1 |
| `ARM_FEEDBACK` | `rt/arm_Feedback` | 机械臂反馈 | G1 |
| `ULIDAR_SWITCH` | `rt/utlidar/switch` | LiDAR开关 | Go2 |
| `ULIDAR` | `rt/utlidar/voxel_map` | LiDAR体素图 | Go2 |
| `ULIDAR_ARRAY` | `rt/utlidar/voxel_map_compressed` | LiDAR压缩点云 | Go2 |
| `ULIDAR_STATE` | `rt/utlidar/lidar_state` | LiDAR状态 | Go2 |
| `AUDIO_HUB_REQ` | `rt/api/audiohub/request` | 音频Hub请求 | Go2 |
| `AUDIO_HUB_PLAY_STATE` | `rt/audiohub/player/state` | 音频播放状态 | Go2 |
| `FRONT_PHOTO_REQ` | `rt/api/videohub/request` | 视频请求 | Go2 |

### SPORT_CMD

| 常量 | api_id | 说明 |
|------|--------|------|
| `Damp` | 1001 | 阻尼模式 |
| `BalanceStand` | 1002 | 平衡站立 |
| `StopMove` | 1003 | 停止移动 |
| `StandUp` | 1004 | 站起 |
| `StandDown` | 1005 | 趴下 |
| `RecoveryStand` | 1006 | 恢复站立 |
| `Euler` | 1007 | 欧拉角调整 |
| `Move` | 1008 | 移动 |
| `Sit` | 1009 | 坐下 |
| `RiseSit` | 1010 | 从坐姿站起 |
| `SwitchGait` | 1011 | 切换步态 |
| `Trigger` | 1012 | 触发 |
| `BodyHeight` | 1013 | 身体高度 |
| `FootRaiseHeight` | 1014 | 抬脚高度 |
| `SpeedLevel` | 1015 | 速度等级 |
| `Hello` | 1016 | 招手 |
| `Stretch` | 1017 | 伸展 |
| `TrajectoryFollow` | 1018 | 轨迹跟踪 |
| `ContinuousGait` | 1019 | 连续步态 |
| `Content` | 1020 | 满足动作 |
| `Wallow` | 1021 | 打滚 |
| `Dance1` | 1022 | 跳舞1 |
| `Dance2` | 1023 | 跳舞2 |
| `GetBodyHeight` | 1024 | 获取身体高度 |
| `GetFootRaiseHeight` | 1025 | 获取抬脚高度 |
| `GetSpeedLevel` | 1026 | 获取速度等级 |
| `SwitchJoystick` | 1027 | 切换手柄 |
| `Pose` | 1028 | 姿势调整 |
| `Scrape` | 1029 | 刮地 |
| `FrontFlip` | 1030 | 前空翻 |
| `FrontJump` | 1031 | 前跳 |
| `FrontPounce` | 1032 | 前扑 |
| `WiggleHips` | 1033 | 扭屁股 |
| `GetState` | 1034 | 获取状态 |
| `EconomicGait` | 1035 | 经济步态 |
| `FingerHeart` | 1036 | 比心 |
| `StandOut` | 1039 | AI动作状态 |
| `FreeWalk` | 1045 | 自由行走 |
| `LeadFollow` | 1045 | 跟随 |
| `Standup` | 1050 | 站立 |
| `CrossWalk` | 1051 | 交叉行走 |
| `CrossStep` | 1302 | 交叉步 (AI) |
| `OnesidedStep` | 1303 | 单侧步 (AI) |
| `Bound` | 1304 | 弹跳 (AI) |
| `MoonWalk` | 1305 | 太空步 (AI) |
| `Handstand` | 1301 | 倒立 (AI) |
| `LeftFlip` | 1042 | 左空翻 |
| `RightFlip` | 1043 | 右空翻 |
| `BackFlip` | 1044 | 后空翻 |

### VUI_COLOR

| 常量 | 值 |
|------|----|
| `WHITE` | `"white"` |
| `RED` | `"red"` |
| `YELLOW` | `"yellow"` |
| `BLUE` | `"blue"` |
| `GREEN` | `"green"` |
| `CYAN` | `"cyan"` |
| `PURPLE` | `"purple"` |

### AUDIO_API

| 常量 | api_id | 说明 |
|------|--------|------|
| `GET_AUDIO_LIST` | 1001 | 获取音频列表 |
| `SELECT_START_PLAY` | 1002 | 选择并播放 |
| `PAUSE` | 1003 | 暂停 |
| `UNSUSPEND` | 1004 | 恢复播放 |
| `SELECT_PREV_START_PLAY` | 1005 | 上一首 |
| `SELECT_NEXT_START_PLAY` | 1006 | 下一首 |
| `SET_PLAY_MODE` | 1007 | 设置播放模式 |
| `SELECT_RENAME` | 1008 | 重命名 |
| `SELECT_DELETE` | 1009 | 删除 |
| `GET_PLAY_MODE` | 1010 | 获取播放模式 |
| `UPLOAD_AUDIO_FILE` | 2001 | 上传音频文件 |
| `PLAY_START_OBSTACLE_AVOIDANCE` | 3001 | 播报进入避障 |
| `PLAY_EXIT_OBSTACLE_AVOIDANCE` | 3002 | 播报退出避障 |
| `PLAY_START_COMPANION_MODE` | 3003 | 播报进入陪伴 |
| `PLAY_EXIT_COMPANION_MODE` | 3004 | 播报退出陪伴 |
| `ENTER_MEGAPHONE` | 4001 | 进入扩音器 |
| `EXIT_MEGAPHONE` | 4002 | 退出扩音器 |
| `UPLOAD_MEGAPHONE` | 4003 | 上传扩音器音频 |
| `INTERNAL_LONG_CORPUS_SELECT_TO_PLAY` | 5001 | 内部长语料播放 |
| `INTERNAL_LONG_CORPUS_PLAYBACK_COMPLETED` | 5002 | 播放完成 |
| `INTERNAL_LONG_CORPUS_STOP_PLAYING` | 5003 | 停止播放 |

### DATA_CHANNEL_TYPE

| 常量 | 值 | 说明 |
|------|----|------|
| `VALIDATION` | `"validation"` | 验证 |
| `SUBSCRIBE` | `"subscribe"` | 订阅 |
| `UNSUBSCRIBE` | `"unsubscribe"` | 取消订阅 |
| `MSG` | `"msg"` | 消息 |
| `REQUEST` | `"req"` | 请求 |
| `RESPONSE` | `"res"` | 响应 |
| `VID` | `"vid"` | 视频 |
| `AUD` | `"aud"` | 音频 |
| `ERR` | `"err"` | 错误 |
| `HEARTBEAT` | `"heartbeat"` | 心跳 |
| `RTC_INNER_REQ` | `"rtc_inner_req"` | RTC内部请求 |
| `RTC_REPORT` | `"rtc_report"` | RTC报告 |
| `ADD_ERROR` | `"add_error"` | 添加错误 |
| `RM_ERROR` | `"rm_error"` | 移除错误 |
| `ERRORS` | `"errors"` | 错误列表 |

---

## 7. 错误码参考

错误通过数据通道自动推送，格式为 `[timestamp, error_source, error_code]`。

### 通信固件故障 (source=100)

| 错误码 | 说明 |
|--------|------|
| `100_1` | DDS消息超时 |
| `100_2` | 分配开关异常 |
| `100_10` | 电池通信错误 |
| `100_20` | 运动控制通信异常 |
| `100_40` | MCU通信错误 |
| `100_80` | 电机通信错误 |

### 通信固件故障 (source=200)

| 错误码 | 说明 |
|--------|------|
| `200_1` | 后左风扇卡住 |
| `200_2` | 后右风扇卡住 |
| `200_4` | 前风扇卡住 |

### 电机故障 (source=300)

| 错误码 | 说明 |
|--------|------|
| `300_1` | 过流 |
| `300_2` | 过压 |
| `300_4` | 驱动器过热 |
| `300_8` | 母线欠压 |
| `300_10` | 绕组过热 |
| `300_20` | 编码器异常 |
| `300_100` | 电机通信中断 |

### 雷达故障 (source=400)

| 错误码 | 说明 |
|--------|------|
| `400_1` | 电机转速异常 |
| `400_2` | 点云数据异常 |
| `400_4` | 串口数据异常 |
| `400_10` | 脏污指数异常 |

### UWB故障 (source=500)

| 错误码 | 说明 |
|--------|------|
| `500_1` | UWB串口打开异常 |
| `500_2` | 机器人信息检索异常 |

### 运动控制 (source=600)

| 错误码 | 说明 |
|--------|------|
| `600_4` | 过热软件保护 |
| `600_8` | 低电量软件保护 |

### 轮式电机异常

| 错误码 | 说明 |
|--------|------|
| `wheel_300_40` | 校准数据异常 |
| `wheel_300_80` | 异常复位 |
| `wheel_300_100` | 电机通信中断 |

---

## 8. 完整示例代码集

所有示例代码位于项目的 `examples/` 目录。

| # | 示例 | 路径 | 机型 |
|---|------|------|------|
| 1 | 运动控制 (Hello/Move/AI模式) | `examples/go2/data_channel/sportmode/sportmode.py` | Go2 |
| 2 | VUI 灯光音量控制 | `examples/go2/data_channel/vui/vui.py` | Go2 |
| 3 | 低级状态订阅 | `examples/go2/data_channel/lowstate/lowstate.py` | Go2 |
| 4 | 多重状态订阅 | `examples/go2/data_channel/multiplestate/multiplestate.py` | Go2 |
| 5 | 运动模式状态订阅 | `examples/go2/data_channel/sportmodestate/sportmodestate.py` | Go2 |
| 6 | LiDAR 点云流 | `examples/go2/data_channel/lidar/lidar_stream.py` | Go2 |
| 7 | LiDAR 3D可视化 | `examples/go2/data_channel/lidar/plot_lidar_stream.py` | Go2 |
| 8 | 实时音频接收 | `examples/go2/audio/live_audio/live_recv_audio.py` | Go2 |
| 9 | 音频播放器 (AudioHub) | `examples/go2/audio/mp3_player/webrtc_audio_player.py` | Go2 |
| 10 | MP3 播放到机器人 | `examples/go2/audio/mp3_player/play_mp3.py` | Go2 |
| 11 | 保存音频到文件 | `examples/go2/audio/save_audio/save_audio_to_file.py` | Go2 |
| 12 | 网络电台播放 | `examples/go2/audio/internet_radio/stream_radio.py` | Go2 |
| 13 | 摄像头视频流 | `examples/go2/video/camera_stream/display_video_channel.py` | Go2 |
| 14 | G1 机械臂+手柄+行走 | `examples/g1/data_channel/sport_mode/sportmode.py` | G1 |
