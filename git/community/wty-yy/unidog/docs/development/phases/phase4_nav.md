# 阶段四: 导航 + 避障

**预计时间**: 1-2 周  
**目标**: 实现自主导航到目标点 + 雷达实时避障

---

## 里程碑

- [ ] Nav2 全局规划器配置完成
- [ ] DWB 局部规划器配置完成
- [ ] DWA 避障功能启用
- [ ] 点击地图目标点自动导航
- [ ] 动态障碍自动绕行
- [ ] 导航状态实时显示

---

## 详细步骤

### Step 4.1: 安装 Nav2

```bash
# Nav2 应该已经在阶段一安装了
# 验证安装
source /opt/ros/humble/setup.bash
ros2 pkg list | grep nav2
```

### Step 4.2: 创建 Nav2 配置文件

创建: `~/git/ros2_ws/src/nav2_bringup/config/go2_nav2.yaml`

```yaml
amcl:
  ros__parameters:
    use_sim_time: False
    alpha1: 0.2
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2
    alpha5: 0.2
    base_frame_id: "base_link"
    beacon_frame_id: "beacon"
    global_frame_id: "map"
    lambda_short: 0.1
    laser_likelihood_max_dist: 2.0
    laser_max_range: 10.0
    laser_min_range: 0.2
    max_beams: 30
    max_particles: 2000
    min_particles: 500
    odom_frame_id: "odom"
    pf_err: 0.05
    pf_z: 0.4
    recovery_alpha_fast: 0.0
    recovery_alpha_slow: 0.0
    resample_interval: 1
    robot_model_type: "nav2_amcl::OmniMotionLib"
    save_pose_rate: 0.5
    sigma_hit: 0.2
    tf_broadcast: True
    transform_tolerance: 1.0
    update_min_a: 0.2
    update_min_d: 0.25
    z_hit: 0.5
    z_max: 0.05
    z_rand: 0.5
    z_short: 0.05

bt_navigator:
  ros__parameters:
    use_sim_time: True
    global_frame_id: "map"
    robot_base_frame: "base_link"
    odom_topic: "/odom"
    default_bt_xml_filename: "navigate_w_replanning_and_recovery.xml"
    plugin_lib_names:
      - nav2_behavior_tree

controller_server:
  ros__parameters:
    use_sim_time: True
    controller_frequency: 20.0
    min_x_velocity_threshold: 0.001
    min_y_velocity_threshold: 0.001
    min_theta_velocity_threshold: 0.001
    progress_checker_plugin: "progress_checker"
    goal_checker_plugin: "goal_checker"
    controller_plugins: ["FollowPath"]
    
    FollowPath:
      plugin: "dwb_core/DWBFollower"
      critics:
        - "BaseObstacleCritical"
        - "GoalCritic"
        - "PathAlignCritic"
        - "PathDistCritic"
        - "ReachGoalCritic"
        - "RotateToGoalCritic"
        - "OscillationCritic"
      BaseObstacleCritical.scale: 1.0
      PathAlignCritic.scale: 4.0
      PathDistCritic.scale: 32.0

planner_server:
  ros__parameters:
    use_sim_time: True
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "nav2_smac_planner/SmacPlanner"
      tolerance: 0.5
      neutral_cost: 50
      cost_scale_factor: 2.0
```

### Step 4.3: 启动 Nav2 导航

```bash
# 创建启动文件: ~/git/ros2_ws/src/nav2_bringup/launch/go2_nav.launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Map server (加载已保存的地图)
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            parameters=[{'yaml_filename': 'map.yaml'}]
        ),
        
        # AMCL 定位
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            parameters=['config/go2_nav2.yaml']
        ),
        
        # 规划器
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            parameters=['config/go2_nav2.yaml']
        ),
        
        # 控制器
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            parameters=['config/go2_nav2.yaml']
        ),
        
        # BT Navigator
        Node(
            package='nav2_behaviors',
            executable='bt_navigator',
            name='bt_navigator',
            parameters=['config/go2_nav2.yaml']
        ),
        
        # 生命周期管理
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager',
            parameters=[{'autostart': True}]
        ),
    ])
```

### Step 4.4: 修改 WebSocket Bridge 支持导航

```python
# 添加导航 Action 客户端

from action_tutorials_interfaces.action import Fibonacci
from rclpy.action import ActionClient

class NavigationClient(Node):
    def __init__(self):
        super().__init__('nav_client')
        self._action_client = ActionClient(
            self,
            Fibonacci,  # 或自定义 NavigateToPose
            '/navigate_to_pose'
        )
    
    def send_goal(self, x, y, yaw=0.0):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        
        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback
        )
```

### Step 4.5: 网页目标点导航

```typescript
// 在地图上点击设置目标点
canvas.on('click', (event) => {
  const rect = canvas.getBoundingClientRect()
  const x = (event.clientX - rect.left) / scale  // 像素 → 米
  const y = (event.clientY - rect.top) / scale
  
  // 发送到 MCP Server / Navigation Client
  websocket.send(JSON.stringify({
    type: 'navigate_to',
    x,
    y
  }))
})
```

### Step 4.6: 避障配置与测试

```yaml
# DWB 避障参数
dwb_core:
  ros__parameters:
    # 避障参数
    BaseObstacleCritical:
      scale: 1.0
      critic_default_params:
        batch_size: 500
        use_odom: True
    
    # 局部规划窗口
    PathDistCritic:
      scale: 32.0
      critic_default_params:
        scale: 5.0
    
    # 速度限制
    max_vel_x: 0.5
    max_vel_x_backwards: 0.2
    max_vel_theta: 1.0
    
    # 避障相关
    forward_prune: True
    short_circuit_trajectory: True
```

### Step 4.7: 端到端导航测试

```bash
# 1. 确保地图已保存
# 2. 启动仿真器
cd ~/git/official/unitree_mujoco/simulate/build
./unitree_mujoco

# 3. 启动 wty-yy
cd ~/git/community/wty-yy/unitree_cpp_deploy/deploy/robots/go2/build
./go2_ctrl -n lo

# 4. 启动 Nav2
cd ~/git/ros2_ws
source install/setup.bash
ros2 launch nav2_bringup go2_nav.launch.py

# 5. 启动 WebSocket Bridge
python3 websocket_bridge/bridge.py

# 6. 浏览器访问
# 在地图上点击一个点, 狗应该自动走过去
```

---

## 验收标准

| 检查项 | 预期结果 | 验证方法 |
|--------|---------|---------|
| Nav2 启动 | 无报错 | 终端输出 |
| 全局规划 | 显示路径 | RViz 查看 |
| /cmd_vel 输出 | 有速度指令 | `ros2 topic echo /cmd_vel` |
| 点击导航 | 狗自主走到目标点 | 眼睛观察 |
| 避障 | 人为挡路狗绕行 | 实际测试 |

---

## 下一步

阶段四完成后 → [阶段五: 语音+MCP控制](./phase5_voice.md)
