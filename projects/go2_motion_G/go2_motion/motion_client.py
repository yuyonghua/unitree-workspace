import time
import threading
import numpy as np
from enum import Enum

from go2_motion.config import Go2Config
from go2_motion.comm.dds_comm import DDSComm
from go2_motion.control.safety import SafetyManager
from go2_motion.policy.obs_builder import ObsBuilder
from go2_motion.policy.rl_policy import RLPolicy
from go2_motion.policy.stand_policy import StandPolicy


class MotionState(Enum):
    IDLE = 0
    DAMPING = 1
    STANDING = 2
    WALKING = 3
    LYING = 4


class MotionClient:
    """
    高级运动控制接口 (类似官方 SportClient)。
    
    内部管理 DDS 通信、观测构建、RL 推理以及 50Hz 控制循环。
    对外暴露简单的方法: Move(), StandUp(), Damp(), 自动处理状态切换。
    """
    def __init__(self, config: Go2Config):
        self.config = config
        
        # 核心组件
        self.comm = DDSComm(config)
        self.safety = SafetyManager(config)
        self.obs_builder = ObsBuilder(config)
        
        # 策略
        self.rl_policy = RLPolicy(config)
        self.stand_policy = StandPolicy(config)
        
        # 状态
        self._state = MotionState.IDLE
        self._running = False
        self._control_thread = None
        self._cmd = np.zeros(3, dtype=np.float32)  # [vx, vy, vyaw]
        self._cmd_lock = threading.Lock()
        
        # 内部上下文
        self.last_action = np.zeros(self.config.num_actions, dtype=np.float32)
        
    def Init(self):
        """初始化通信和策略"""
        self.comm.init()
        if not self.comm.wait_for_connection():
            raise RuntimeError("Failed to connect to robot/simulator via DDS.")
        
    def Move(self, vx: float, vy: float, vyaw: float):
        """
        发送速度指令并切换到 WALKING 状态。
        """
        with self._cmd_lock:
            self._cmd = np.array([vx, vy, vyaw], dtype=np.float32)
        
        if self._state != MotionState.WALKING:
            self._transition_to(MotionState.WALKING)
            
    def StandUp(self):
        """站立在原地 (不发送运动指令，由 StandPolicy 处理或使用零速度 RL)"""
        with self._cmd_lock:
            self._cmd = np.zeros(3, dtype=np.float32)
            
        if self._state != MotionState.STANDING:
            self._transition_to(MotionState.STANDING)
            
    def Damp(self):
        """进入阻尼模式 (安全掉电状态)"""
        self._transition_to(MotionState.DAMPING)
        
    def Start(self):
        """启动后台 50Hz 控制循环"""
        if self._running:
            return
            
        self._running = True
        self._control_thread = threading.Thread(
            target=self._control_loop, 
            name="motion_client_loop",
            daemon=True
        )
        self._control_thread.start()
        print("[MotionClient] Control loop started.")
        
    def Stop(self):
        """停止控制循环并进入阻尼模式"""
        self._running = False
        if self._control_thread:
            self._control_thread.join()
        self.Damp()
        print("[MotionClient] Control loop stopped.")
        
    def _transition_to(self, new_state: MotionState):
        """简单的状态切换"""
        if self._state == new_state:
            return
            
        print(f"[MotionClient] Transition: {self._state.name} -> {new_state.name}")
        self._state = new_state
        
        if new_state == MotionState.DAMPING:
            # 清除之前的 action
            self.last_action = np.zeros(self.config.num_actions, dtype=np.float32)

    def _control_loop(self):
        """50Hz 核心控制循环"""
        dt = self.config.control_dt
        next_tick = time.perf_counter()
        
        while self._running:
            # 1. 严格周期开始
            tick_start = time.perf_counter()
            
            # 2. 获取最新机器人原始状态
            state = self.comm.get_state()
            if not state.is_valid():
                # 等待直到接收到第一帧数据
                time.sleep(0.001)
                next_tick = time.perf_counter() + dt
                continue
                
            # 3. 状态机逻辑
            if self._state == MotionState.DAMPING:
                self.comm.send_damping_cmd()
                
            elif self._state in (MotionState.STANDING, MotionState.WALKING):
                # 获取最新的控制指令 (非阻塞)
                with self._cmd_lock:
                    current_cmd = self._cmd.copy()
                    
                # a. 构建模型输入
                obs = self.obs_builder.build(state, current_cmd, self.last_action)
                
                # b. 策略分支
                if self._state == MotionState.STANDING:
                    # 站立模式下，如果指令全为零，也可以尝试使用 RL 策略 (RL 策略通常包含站立)
                    # 或者使用内置的 PD 站立策略以保稳
                    action = self.stand_policy.compute_action(obs)
                else:
                    # 使用 RL 策略核心
                    action = self.rl_policy.compute_action(obs)
                    
                # c. 计算目标角度并进行安全限位
                target_q = self.config.default_angles + action * self.config.action_scale
                target_q = self.safety.clip_target_position(target_q)
                
                # d. 下发底层指令 (kps/kds 对齐原项目)
                self.comm.send_position_cmd(
                    target_q=target_q,
                    kps=self.config.kps,
                    kds=self.config.kds
                )
                
                # e. 更新上下文动作 (用于下一次 obs 构建)
                self.last_action = action
                
            else:
                self.comm.send_damping_cmd()
                
            # 4. 精确频率控制
            next_tick += dt
            sleep_time = next_tick - time.perf_counter()
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # 超过周期处理
                if abs(sleep_time) > dt:
                    # 如果落后太多，重置 next_tick 避免追赶效应
                    next_tick = time.perf_counter()
                
                # 打印延迟警告 (仅在 WALKING 状态下)
                if self._state == MotionState.WALKING and abs(sleep_time) > 0.005:
                    print(f"[Warning] Control loop slow! Lag: {abs(sleep_time)*1000:.1f}ms")
