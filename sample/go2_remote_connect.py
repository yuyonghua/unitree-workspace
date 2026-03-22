import asyncio
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod, RTC_TOPIC, SPORT_CMD

async def main():
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.Remote,
        serialNumber="B42N6000Q1496588",
        username="yyhstd@qq.com",
        password="Yuyh0102"
    )
    
    print("正在连接...")
    await conn.connect()
    
    if conn.isConnected:
        print("\n✅ 登录验证成功！已连接到机器人\n")
        
        print("发送站起命令...")
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["StandUp"]}
        )
        print("🐕 机器人已站起\n")
        
        await asyncio.sleep(3)
        
        print("发送坐下命令...")
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["Sit"]}
        )
        print("🐕 机器人已坐下\n")
        
        await asyncio.sleep(2)
        
        print("再次发送站起命令...")
        await conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["StandUp"]}
        )
        print("🐕 机器人已站起\n")
        
    else:
        print("❌ 连接失败")
    
    print("正在断开连接...")
    await conn.disconnect()
    print("已断开连接")

asyncio.run(main())
