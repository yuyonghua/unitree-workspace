# Go2 WebRTC 无线控制开发指南

---

## 验证信息

| 项目 | 详情 |
|------|------|
| 机型 | Go2-X |
| 环境 | Windows + WSL + conda + Python 3.10 |
| 方式 | WiFi 热点 + WebRTC 协议 |
| 库 | unitree-webrtc-connect v2.0.4 |
| 网络 | Go2 和电脑连接同一 WiFi 热点 |
| 实测 IP | 10.114.97.227 |
| **结论** | **✅ 可行，PRO / X / EDU 均支持此方式** |

---

## PRO / X / EDU 三型号对比

### 硬件与价格

| 特性 | PRO | X | EDU |
|------|-----|---|-----|
| 价格 | ~¥16,500 | ~¥28,999 | ~¥50,000+ |
| 电池 | 8000mAh (1-2h) | 8000mAh (1-2h) | 15000mAh (2-4h) |
| 算力模组 | ❌ | ❌ | NVIDIA Orin (40-100 TOPS) |
| 深度相机 | ❌ | ❌ | ✅ D435i |
| 足端力传感器 | ❌ | ⚠️ 支持扩展 | ✅ 标配 |
| 拓展坞 | ❌ | ❌ | ✅ |

### 开发方式对比

| 开发方式 | PRO | X | EDU |
|----------|-----|---|-----|
| APP 控制 | ✅ | ✅ | ✅ |
| WebRTC 无线开发 | ✅ | ✅ | ✅ |
| 有线 SDK (应用层) | ❌ | ✅ | ✅ |
| 有线 DDS (底层) | ❌ | ❌ | ✅ |
| 本地模型训练部署 | ❌ | ❌ | ✅ |

### WebRTC vs DDS 能力边界

| 能力 | WebRTC (PRO/X/EDU 均可) | DDS (仅 EDU) |
|------|-------------------------|--------------|
| 高层运动控制 | ✅ | ✅ |
| 摄像头视频流 | ✅ | ✅ |
| LiDAR 点云 | ✅ | ✅ |
| IMU 数据 | ✅ | ✅ |
| 音频收发 | ✅ (PRO/EDU) | ✅ |
| 底层关节控制 | ❌ | ✅ |
| 自定义步态 | ❌ | ✅ |
| 足端力数据 | ❌ | ✅ |
| 连接方式 | WiFi / 热点 | 网线 + 拓展坞 |
| 系统要求 | Win / Mac / Linux | 仅 Ubuntu |

---

## 环境搭建

```bash
# 创建 conda 环境
conda create -n go2 python=3.10
conda activate go2

# 安装依赖（一行搞定）
pip install unitree-webrtc-connect
```

无需编译，无需 cmake，无需 C++。

---

## 网络配置

1. Go2 开机，通过 APP 连接 WiFi 热点
2. 电脑连接同一热点
3. 获取 Go2 在热点下的 IP（APP 内查看或路由器后台）
4. 实测 IP：`10.114.97.227`，通用格式：`192.168.1.xxx`

---

## 快速上手

```python
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD
import asyncio

async def main():
    # 替换为你的 Go2 IP
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.1.xxx")
    await conn.connect()

    # 站起
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"],
        {"api_id": SPORT_CMD["RecoveryStand"]}
    )

    # 前进 0.5 m/s
    await conn.datachannel.pub_sub.publish_request_new(
        RTC_TOPIC["SPORT_MOD"],
        {"api_id": SPORT_CMD["Move"], "parameter": {"x": 0.5, "y": 0, "z": 0}}
    )

asyncio.run(main())
```

---

## 常用运动命令

| 命令 | SPORT_CMD | 说明 |
|------|-----------|------|
| Move | `{"x": vx, "y": vy, "z": vz}` | 前后左右 + 旋转 |
| StopMove | 无参数 | 停止移动 |
| StandUp | 无参数 | 站起 |
| StandDown | 无参数 | 趴下 |
| RecoveryStand | 无参数 | 恢复站立 |

---

## 附: keyboard_control.py

同目录下的键盘控制脚本，基于 Go2-X 实测验证，可直接运行参考。

---

## 更多参考

- PyPI: https://pypi.org/project/unitree-webrtc-connect/
- GitHub: https://github.com/legion1581/go2_webrtc_connect
- go2-webrtc (另一个库): https://github.com/tfoldi/go2-webrtc
