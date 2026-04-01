# 阶段二: Web 可视化基础

**预计时间**: 2 周  
**目标**: 在浏览器中实时显示机器狗状态、雷达点云和地图数据

---

## 里程碑

- [ ] WebSocket Bridge 开发完成并运行
- [ ] 浏览器能连接到 WebSocket Bridge
- [ ] 3D 点云实时渲染 (Three.js)
- [ ] 机器狗 3D 模型显示
- [ ] 2D 地图渲染 (Canvas)
- [ ] 状态数据面板显示

---

## 详细步骤

### Step 2.1: 创建 WebSocket Bridge

创建文件: `~/git/community/unidog_ws/websocket_bridge/bridge.py`

```python
#!/usr/bin/env python3
"""
UniDog WebSocket Bridge
订阅 ROS2 Topic, 通过 WebSocket 转发到浏览器
"""

import asyncio
import json
import struct
from websockets.server import serve
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, OccupancyGrid
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist

class LidarBridge(Node):
    def __init__(self):
        super().__init__('lidar_bridge')
        self.websocket_clients = set()
        
        # 订阅 ROS2 Topic
        self.create_subscription(
            PointCloud2,
            '/utlidar/cloud',
            self.on_lidar_data,
            10
        )
        self.create_subscription(
            Odometry,
            '/odom',
            self.on_odom_data,
            10
        )
        self.create_subscription(
            OccupancyGrid,
            '/map',
            self.on_map_data,
            10
        )
        
    def on_lidar_data(self, msg):
        # 将 PointCloud2 转为二进制
        points = self.read_points(msg)
        binary = struct.pack(f'{len(points)}f', *points.flatten())
        
        # 广播给所有客户端
        for client in self.websocket_clients:
            asyncio.create_task(client.send(binary))
    
    def on_odom_data(self, msg):
        data = {
            'type': 'odom',
            'position': {
                'x': msg.pose.pose.position.x,
                'y': msg.pose.pose.position.y,
                'z': msg.pose.pose.position.z
            },
            'orientation': {
                'x': msg.pose.pose.orientation.x,
                'y': msg.pose.pose.orientation.y,
                'z': msg.pose.pose.orientation.z,
                'w': msg.pose.pose.orientation.w
            }
        }
        for client in self.websocket_clients:
            asyncio.create_task(client.send(json.dumps(data)))
    
    async def handle_client(self, websocket):
        self.websocket_clients.add(websocket)
        try:
            async for message in websocket:
                # 接收遥控指令
                cmd = json.loads(message)
                if cmd['type'] == 'cmd_vel':
                    self.publish_cmd_vel(cmd)
        finally:
            self.websocket_clients.remove(websocket)
    
    def publish_cmd_vel(self, cmd):
        # 发布到 ROS2 /cmd_vel
        # 实现代码...
    
    def read_points(self, msg):
        # PointCloud2 解析代码
        import numpy as np
        # ... 实现
        return np.array([])

async def main():
    rclpy.init()
    bridge = LidarBridge()
    
    # 启动 WebSocket 服务器
    async with serve(bridge.handle_client, '0.0.0.0', 8765):
        print("WebSocket Bridge started on ws://0.0.0.0:8765")
        rclpy.spin(bridge)

if __name__ == '__main__':
    asyncio.run(main())
```

### Step 2.2: 创建 Vue3 前端项目

```bash
cd ~/git/community/unidog_ws/web

# 使用 Vite 创建项目
pnpm create vite@latest . --template vue-ts

# 安装依赖
pnpm install
pnpm add three @types/three nipplejs pinia

# 启动开发服务器
pnpm dev --host 0.0.0.0 --port 8080
```

### Step 2.3: 实现 3D 点云渲染 (Three.js)

创建文件: `~/git/community/unidog_ws/web/src/components/PointCloud3D.vue`

```typescript
<template>
  <div ref="container" class="pointcloud-3d"></div>
</template>

<script setup lang="ts">
import * as THREE from 'three'

const container = ref<HTMLElement>()
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let pointCloud: THREE.Points

onMounted(() => {
  initThree()
  animate()
})

function initThree() {
  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)
  
  // 创建相机
  camera = new THREE.PerspectiveCamera(
    75,
    container.value!.clientWidth / container.value!.clientHeight,
    0.1,
    1000
  )
  camera.position.set(0, 2, 5)
  
  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(container.value!.clientWidth, container.value!.clientHeight)
  container.value!.appendChild(renderer.domElement)
  
  // 创建点云几何体
  const geometry = new THREE.BufferGeometry()
  const positions = new Float32Array(24000 * 3)  // 24000 点
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  
  // 点云材质
  const material = new THREE.PointsMaterial({
    color: 0xff6b6b,
    size: 0.05,
    transparent: true,
    opacity: 0.8
  })
  
  pointCloud = new THREE.Points(geometry, material)
  scene.add(pointCloud)
}

function updatePoints(data: Float32Array) {
  const positions = pointCloud.geometry.attributes.position.array as Float32Array
  positions.set(data)
  pointCloud.geometry.attributes.position.needsUpdate = true
}

function animate() {
  requestAnimationFrame(animate)
  renderer.render(scene, camera)
}
</script>
```

### Step 2.4: 实现 2D Canvas 地图

创建文件: `~/git/community/unidog_ws/web/src/components/GridMap2D.vue`

```vue
<template>
  <canvas ref="canvas" class="gridmap-2d"></canvas>
</template>

<script setup lang="ts">
const canvas = ref<HTMLCanvasElement>()
let ctx: CanvasRenderingContext2D
const scale = 20  // 像素/米

onMounted(() => {
  ctx = canvas.value!.getContext('2d')!
  canvas.value!.width = 800
  canvas.value!.height = 600
})

function drawGrid(gridData: number[][], width: number, height: number) {
  ctx.clearRect(0, 0, canvas.value!.width, canvas.value!.height)
  
  for (let x = 0; x < width; x++) {
    for (let y = 0; y < height; y++) {
      const value = gridData[x][y]
      let color = '#888'  // 未知: 灰色
      
      if (value === 2) color = '#333'  // 占用: 黑色
      else if (value === 1) color = '#fff'  // 空闲: 白色
      
      ctx.fillStyle = color
      ctx.fillRect(x * scale, y * scale, scale, scale)
    }
  }
}

function drawRobot(x: number, y: number, yaw: number) {
  ctx.save()
  ctx.translate(x * scale, y * scale)
  ctx.rotate(-yaw)
  
  ctx.fillStyle = '#4ecdc4'
  ctx.beginPath()
  ctx.arc(0, 0, scale * 0.3, 0, Math.PI * 2)
  ctx.fill()
  
  // 朝向指示线
  ctx.strokeStyle = '#fff'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(0, 0)
  ctx.lineTo(scale, 0)
  ctx.stroke()
  
  ctx.restore()
}
</script>
```

### Step 2.5: 实现遥控方向杆

```typescript
import nipplejs from 'nipplejs'

function setupJoystick() {
  const manager = nipplejs.create({
    zone: document.getElementById('joystick-zone')!,
    mode: 'static',
    position: { left: '50%', top: '50%' },
    color: '#4ecdc4'
  })
  
  manager.on('move', (_, data) => {
    const vx = data.vector.y * 0.5  // 映射到 0.5 m/s
    const omega = -data.vector.x * 1.0  // 映射到 1.0 rad/s
    
    // 发送到 WebSocket
    websocket.send(JSON.stringify({
      type: 'cmd_vel',
      vx,
      vy: 0,
      omega
    }))
  })
  
  manager.on('end', () => {
    websocket.send(JSON.stringify({
      type: 'cmd_vel',
      vx: 0, vy: 0, omega: 0
    }))
  })
}
```

### Step 2.6: WebSocket 客户端

```typescript
const WS_URL = 'ws://localhost:8765'

async function connectWebSocket() {
  const ws = new WebSocket(WS_URL)
  
  ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
      // 点云二进制数据
      event.data.arrayBuffer().then(buffer => {
        const points = new Float32Array(buffer)
        pointCloud3D.updatePoints(points)
      })
    } else {
      // JSON 数据
      const msg = JSON.parse(event.data)
      if (msg.type === 'odom') {
        updateRobotPose(msg.position, msg.orientation)
      } else if (msg.type === 'gridmap') {
        gridMap2D.drawGrid(msg.data, msg.width, msg.height)
      }
    }
  }
  
  ws.onopen = () => {
    console.log('WebSocket connected')
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}
```

---

## 验收标准

| 检查项 | 预期结果 | 验证方法 |
|--------|---------|---------|
| WebSocket Bridge | 服务启动无报错 | 查看终端输出 |
| 浏览器连接 | ws://localhost:8765 能连接 | 浏览器控制台 |
| 3D 点云 | 雷达点云实时显示 | 眼睛观察 |
| 2D 地图 | OccupancyGrid 渲染 | 眼睛观察 |
| 遥控方向杆 | 拖动后狗移动 | 眼睛观察 |

---

## 下一步

阶段二完成后 → [阶段三: 遥控+建图](./phase3_mapping.md)
