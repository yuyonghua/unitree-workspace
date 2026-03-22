import asyncio
import curses
import json
import sys
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

ROBOT_IP = "10.114.97.227"

# 速度参数
MOVE_SPEED = 0.5      # 前后左右速度 (m/s)
ROTATE_SPEED = 0.8    # 旋转速度 (rad/s)

# 按键映射
KEY_UP = 259
KEY_DOWN = 258
KEY_LEFT = 260
KEY_RIGHT = 261
KEY_ESC = 27
KEY_SPACE = 32


class Go2Controller:
    def __init__(self, conn):
        self.conn = conn
        self.vx = 0  # 前后
        self.vy = 0  # 左右
        self.vz = 0  # 旋转
        self.running = True

    async def send_move_command(self):
        """发送移动命令"""
        await self.conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {
                "api_id": SPORT_CMD["Move"],
                "parameter": {"x": self.vx, "y": self.vy, "z": self.vz}
            }
        )

    async def send_stop(self):
        """发送停止命令"""
        self.vx = 0
        self.vy = 0
        self.vz = 0
        await self.conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["StopMove"]}
        )

    async def stand_up(self):
        """站起"""
        await self.conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["StandUp"]}
        )

    async def stand_down(self):
        """趴下"""
        await self.conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["StandDown"]}
        )

    async def recovery_stand(self):
        """恢复站立"""
        await self.conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["SPORT_MOD"],
            {"api_id": SPORT_CMD["RecoveryStand"]}
        )

    async def switch_to_normal(self):
        """切换到普通模式"""
        await self.conn.datachannel.pub_sub.publish_request_new(
            RTC_TOPIC["MOTION_SWITCHER"],
            {"api_id": 1002, "parameter": {"name": "normal"}}
        )

    def handle_key(self, key):
        """处理按键，返回是否需要发送命令"""
        changed = False

        if key == KEY_UP:  # 上 - 前进
            self.vx = MOVE_SPEED
            changed = True
        elif key == KEY_DOWN:  # 下 - 后退
            self.vx = -MOVE_SPEED
            changed = True
        elif key == KEY_LEFT:  # 左 - 左移
            self.vy = MOVE_SPEED
            changed = True
        elif key == KEY_RIGHT:  # 右 - 右移
            self.vy = -MOVE_SPEED
            changed = True
        elif key == ord('q') or key == ord('Q'):  # Q - 左转
            self.vz = ROTATE_SPEED
            changed = True
        elif key == ord('e') or key == ord('E'):  # E - 右转
            self.vz = -ROTATE_SPEED
            changed = True
        elif key == KEY_SPACE:  # 空格 - 停止
            self.vx = 0
            self.vy = 0
            self.vz = 0
            changed = True

        return changed


def draw_ui(stdscr, controller):
    """绘制界面"""
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    title = "Go2 机器人键盘控制"
    stdscr.addstr(1, (w - len(title)) // 2, title, curses.A_BOLD)

    # 操作说明
    instructions = [
        "",
        "┌─────────────────────────────────────────┐",
        "│           按键控制说明                   │",
        "├─────────────────────────────────────────┤",
        "│  ↑      前进                            │",
        "│  ↓      后退                            │",
        "│  ←      左移                            │",
        "│  →      右移                            │",
        "│  Q      左转                            │",
        "│  E      右转                            │",
        "│  空格   停止                            │",
        "│  W      站起                            │",
        "│  S      趴下                            │",
        "│  R      恢复站立                        │",
        "│  N      切换Normal模式                  │",
        "│  ESC    退出                            │",
        "└─────────────────────────────────────────┘",
    ]

    for i, line in enumerate(instructions):
        if i + 2 < h:
            stdscr.addstr(i + 2, 2, line)

    # 当前状态
    status_y = len(instructions) + 4
    if status_y + 5 < h:
        stdscr.addstr(status_y, 2, "当前状态:", curses.A_BOLD)
        stdscr.addstr(status_y + 1, 4, f"前进/后退 (Vx): {controller.vx:+.2f} m/s")
        stdscr.addstr(status_y + 2, 4, f"左移/右移 (Vy): {controller.vy:+.2f} m/s")
        stdscr.addstr(status_y + 3, 4, f"旋转速度 (Vz): {controller.vz:+.2f} rad/s")

    stdscr.refresh()


async def main_async(stdscr):
    """主异步函数"""
    # 设置 curses
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(50)  # 50ms 超时

    # 连接机器人
    stdscr.addstr(0, 0, "正在连接机器人...")
    stdscr.refresh()

    try:
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=ROBOT_IP)
        await conn.connect()
    except Exception as e:
        stdscr.addstr(1, 0, f"连接失败: {e}")
        stdscr.refresh()
        await asyncio.sleep(3)
        return

    controller = Go2Controller(conn)

    # 切换到normal模式
    stdscr.addstr(1, 0, "正在切换到Normal模式...")
    stdscr.refresh()
    await controller.switch_to_normal()
    await asyncio.sleep(5)

    # 站起
    stdscr.addstr(2, 0, "正在站起...")
    stdscr.refresh()
    await controller.stand_up()
    await asyncio.sleep(2)

    # 主循环
    last_key = -1
    move_sent = False

    while controller.running:
        draw_ui(stdscr, controller)

        try:
            key = stdscr.getch()
        except:
            key = -1

        if key == KEY_ESC:
            controller.running = False
            break
        elif key == ord('w') or key == ord('W'):
            await controller.stand_up()
        elif key == ord('s') or key == ord('S'):
            await controller.stand_down()
        elif key == ord('r') or key == ord('R'):
            await controller.recovery_stand()
        elif key == ord('n') or key == ord('N'):
            await controller.switch_to_normal()
        elif key >= 0:
            if controller.handle_key(key):
                await controller.send_move_command()
                move_sent = True
        elif key == -1 and move_sent:
            # 没有按键时，如果之前发送过移动命令，继续发送当前速度
            # 这样可以保持机器人持续移动直到按下停止
            if controller.vx != 0 or controller.vy != 0 or controller.vz != 0:
                await controller.send_move_command()

        await asyncio.sleep(0.05)  # 50ms

    # 退出前停止机器人
    await controller.send_stop()
    await asyncio.sleep(0.5)


def main(stdscr):
    """包装函数"""
    asyncio.run(main_async(stdscr))


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
