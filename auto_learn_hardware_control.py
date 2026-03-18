#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习控制本地硬件系统
集成硬件检测、智能决策、自动控制和持续学习功能
"""

import asyncio
import sys
import os
import json
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.core.agent_manager import agent_manager, AgentType
from backend.src.core.services.device_discovery_service import device_discovery_service
from backend.src.core.services.hardware_data_collector import (
    hardware_data_collector, HardwareDataType, HardwareDataPoint
)
from backend.src.core.services.connection_controller import (
    InfraredController, AppController, BluetoothController
)
from backend.src.core.services.camera_controller import CameraController
from backend.src.core.services.hardware_controller import (
    hardware_controller, advanced_features, SpectrumHardwareController, HardwareConfig
)


class ControlStrategy(Enum):
    """控制策略枚举"""
    REACTIVE = "reactive"       # 反应式控制
    PREDICTIVE = "predictive"   # 预测式控制
    ADAPTIVE = "adaptive"       # 自适应控制
    OPTIMAL = "optimal"         # 最优控制


@dataclass
class LearningState:
    """学习状态"""
    total_decisions: int = 0
    successful_controls: int = 0
    failed_controls: int = 0
    learning_cycles: int = 0
    last_update: str = ""
    performance_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HardwareAction:
    """硬件动作"""
    action_type: str
    device_id: str
    parameters: Dict[str, Any]
    timestamp: datetime
    expected_outcome: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "device_id": self.device_id,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
            "expected_outcome": self.expected_outcome
        }


class AdaptiveLearningEngine:
    """自适应学习引擎"""
    
    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.action_history: List[HardwareAction] = []
        self.success_patterns: Dict[str, List[Dict]] = {}
        self.failure_patterns: Dict[str, List[Dict]] = {}
        self.device_performance: Dict[str, Dict[str, float]] = {}
        self.parameter_optimizations: Dict[str, Dict[str, Any]] = {}
        
    def record_action(self, action: HardwareAction, success: bool, outcome: Optional[Dict] = None):
        """记录动作及其结果"""
        self.action_history.append(action)
        
        device_key = f"{action.device_id}_{action.action_type}"
        
        if success:
            if device_key not in self.success_patterns:
                self.success_patterns[device_key] = []
            self.success_patterns[device_key].append({
                "parameters": action.parameters,
                "outcome": outcome,
                "timestamp": action.timestamp.isoformat()
            })
        else:
            if device_key not in self.failure_patterns:
                self.failure_patterns[device_key] = []
            self.failure_patterns[device_key].append({
                "parameters": action.parameters,
                "outcome": outcome,
                "timestamp": action.timestamp.isoformat()
            })
    
    def learn_optimal_parameters(self, device_id: str, action_type: str) -> Dict[str, Any]:
        """学习最优参数"""
        device_key = f"{device_id}_{action_type}"
        
        if device_key not in self.success_patterns:
            return {}
        
        successful_actions = self.success_patterns[device_key]
        if not successful_actions:
            return {}
        
        # 分析成功动作的参数模式
        parameter_values: Dict[str, List] = {}
        for action in successful_actions:
            for param, value in action["parameters"].items():
                if param not in parameter_values:
                    parameter_values[param] = []
                if isinstance(value, (int, float)):
                    parameter_values[param].append(value)
        
        # 计算最优参数（使用平均值）
        optimal_params = {}
        for param, values in parameter_values.items():
            if values:
                optimal_params[param] = np.mean(values)
        
        self.parameter_optimizations[device_key] = optimal_params
        return optimal_params
    
    def predict_success_probability(self, device_id: str, action_type: str, 
                                   parameters: Dict[str, Any]) -> float:
        """预测动作成功概率"""
        device_key = f"{device_id}_{action_type}"
        
        success_count = len(self.success_patterns.get(device_key, []))
        failure_count = len(self.failure_patterns.get(device_key, []))
        total = success_count + failure_count
        
        if total == 0:
            return 0.5  # 未知情况返回中等概率
        
        base_probability = success_count / total
        
        # 根据参数相似度调整概率
        if device_key in self.success_patterns:
            similar_params_count = 0
            for action in self.success_patterns[device_key]:
                if self._parameters_similar(action["parameters"], parameters):
                    similar_params_count += 1
            
            if similar_params_count > 0:
                similarity_boost = min(0.2, similar_params_count / success_count * 0.2)
                base_probability = min(1.0, base_probability + similarity_boost)
        
        return base_probability
    
    def _parameters_similar(self, params1: Dict, params2: Dict, tolerance: float = 0.1) -> bool:
        """检查两组参数是否相似"""
        common_keys = set(params1.keys()) & set(params2.keys())
        if not common_keys:
            return False
        
        similar_count = 0
        for key in common_keys:
            val1, val2 = params1[key], params2[key]
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if abs(val1 - val2) <= tolerance * max(abs(val1), abs(val2), 1):
                    similar_count += 1
            elif val1 == val2:
                similar_count += 1
        
        return similar_count / len(common_keys) >= 0.7
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习摘要"""
        return {
            "total_actions": len(self.action_history),
            "success_patterns": {k: len(v) for k, v in self.success_patterns.items()},
            "failure_patterns": {k: len(v) for k, v in self.failure_patterns.items()},
            "optimized_parameters": len(self.parameter_optimizations),
            "learning_rate": self.learning_rate
        }


class AutoLearnHardwareControlSystem:
    """自动学习硬件控制系统"""
    
    def __init__(self):
        self.agent_manager = agent_manager
        self.hardware_data_collector = hardware_data_collector
        self.device_discovery_service = device_discovery_service
        self.learning_engine = AdaptiveLearningEngine()
        
        # 控制器
        self.controllers = {
            "infrared": InfraredController(),
            "app": AppController(),
            "bluetooth": BluetoothController(),
            "camera": CameraController(),
            "spectrum": hardware_controller
        }
        
        # 设备管理
        self.devices: List[Dict[str, Any]] = []
        self.device_states: Dict[str, Dict[str, Any]] = {}
        
        # 学习状态
        self.learning_state = LearningState()
        self.is_running = False
        self.control_strategy = ControlStrategy.ADAPTIVE
        
        # 决策队列
        self.decision_queue: queue.Queue = queue.Queue()
        self.control_queue: queue.Queue = queue.Queue()
        
        # 后台任务
        self.tasks: List[asyncio.Task] = []
        
    async def initialize_system(self):
        """初始化系统"""
        print("🚀 初始化自动学习硬件控制系统...")
        
        # 扫描本地硬件
        print("🔍 扫描本地硬件设备...")
        self.devices = await self.device_discovery_service.scan_all_devices()
        print(f"✅ 发现 {len(self.devices)} 个设备")
        
        # 初始化设备状态
        for device in self.devices:
            self.device_states[device["id"]] = {
                "status": device.get("status", "unknown"),
                "connected": device.get("connected", False),
                "last_control": None,
                "control_count": 0,
                "success_count": 0
            }
        
        # 创建智能体
        await self._create_agents()
        
        # 启动硬件数据收集
        await self.hardware_data_collector.start_collection()
        print("✅ 硬件数据收集已启动")
        
        # 设置AI学习回调
        self.hardware_data_collector.set_ai_learning_callback(self._on_hardware_data)
        
        # 启动后台任务
        self.is_running = True
        self.tasks.append(asyncio.create_task(self._decision_loop()))
        self.tasks.append(asyncio.create_task(self._control_loop()))
        self.tasks.append(asyncio.create_task(self._learning_loop()))
        
        print("✅ 系统自动学习控制已启动")
        
    async def _create_agents(self):
        """创建智能体"""
        print("🤖 创建智能体...")
        
        # 创建决策智能体
        decision_agent_id = self.agent_manager.create_agent(
            AgentType.DECISION,
            {"purpose": "adaptive_hardware_decision", "strategy": "multi_criteria"}
        )
        print(f"  ✅ 决策智能体: {decision_agent_id}")
        
        # 创建控制智能体
        control_agent_id = self.agent_manager.create_agent(
            AgentType.CONTROL,
            {"purpose": "precision_hardware_control", "safety_first": True}
        )
        print(f"  ✅ 控制智能体: {control_agent_id}")
        
        # 创建学习智能体
        learning_agent_id = self.agent_manager.create_agent(
            AgentType.LEARNING,
            {"purpose": "continuous_optimization", "algorithm": "reinforcement"}
        )
        print(f"  ✅ 学习智能体: {learning_agent_id}")
        
        # 初始化所有智能体
        for agent_id in [decision_agent_id, control_agent_id, learning_agent_id]:
            await self.agent_manager.initialize_agent(agent_id)
    
    async def _on_hardware_data(self, data: Dict[str, Any]):
        """硬件数据回调 - 用于实时学习"""
        # 将数据放入决策队列进行处理
        await self._analyze_data_for_decision(data)
    
    async def _analyze_data_for_decision(self, data: Dict[str, Any]):
        """分析数据并生成决策"""
        try:
            data_type = data.get("data_type", "unknown")
            device_id = data.get("device_id", "unknown")
            
            # 根据数据类型决定是否需要控制动作
            if data_type == HardwareDataType.SENSORS.value:
                processed = data.get("processed_data", {})
                
                # 检查是否需要调整（例如温度控制）
                temp_normalized = processed.get("temperature_normalized", 0.5)
                if temp_normalized > 0.8:  # 温度过高
                    decision = {
                        "action": "cool_down",
                        "priority": "high",
                        "device_id": device_id,
                        "parameters": {"intensity": 0.8}
                    }
                    self.decision_queue.put(decision)
                    
            elif data_type == HardwareDataType.CONTROLLERS.value:
                # 控制器数据 - 检查是否需要优化
                features = data.get("data_features", {})
                power_feature = features.get("controller_power_consumption_feature", 50)
                
                if power_feature > 55:  # 功耗过高
                    decision = {
                        "action": "optimize_power",
                        "priority": "medium",
                        "device_id": device_id,
                        "parameters": {"target_efficiency": 0.9}
                    }
                    self.decision_queue.put(decision)
                    
        except Exception as e:
            print(f"  ⚠️ 数据分析出错: {e}")
    
    async def _decision_loop(self):
        """决策循环"""
        while self.is_running:
            try:
                # 定期执行主动决策
                await self._proactive_decision()
                
                # 处理队列中的决策
                while not self.decision_queue.empty():
                    try:
                        decision = self.decision_queue.get_nowait()
                        await self._execute_decision(decision)
                    except queue.Empty:
                        break
                
                await asyncio.sleep(2)  # 决策间隔
                
            except Exception as e:
                print(f"  ❌ 决策循环出错: {e}")
                await asyncio.sleep(5)
    
    async def _proactive_decision(self):
        """主动决策 - 基于当前系统状态"""
        try:
            # 获取当前硬件状态
            hardware_status = await self._get_hardware_status()
            
            # 构建决策上下文
            context = {
                "timestamp": datetime.now().isoformat(),
                "hardware_status": hardware_status,
                "device_states": self.device_states,
                "learning_summary": self.learning_engine.get_learning_summary()
            }
            
            # 执行决策智能体
            decision_results = await self.agent_manager.execute_all_active_agents({
                "decision_input": context
            })
            
            # 根据决策结果生成控制动作
            for result in decision_results:
                if isinstance(result, dict) and result.get("action"):
                    control_action = {
                        "action": result["action"],
                        "device_id": result.get("device_id", "auto"),
                        "parameters": result.get("parameters", {}),
                        "priority": result.get("priority", "low")
                    }
                    self.control_queue.put(control_action)
                    
        except Exception as e:
            print(f"  ⚠️ 主动决策出错: {e}")
    
    async def _execute_decision(self, decision: Dict[str, Any]):
        """执行决策"""
        print(f"🧠 执行决策: {decision.get('action')} (优先级: {decision.get('priority', 'low')})")
        
        # 将决策转换为控制动作
        control_action = {
            "action": decision["action"],
            "device_id": decision.get("device_id", "auto"),
            "parameters": decision.get("parameters", {}),
            "priority": decision.get("priority", "low")
        }
        self.control_queue.put(control_action)
        
        self.learning_state.total_decisions += 1
    
    async def _control_loop(self):
        """控制循环"""
        while self.is_running:
            try:
                # 处理控制队列
                while not self.control_queue.empty():
                    try:
                        action = self.control_queue.get_nowait()
                        await self._execute_control_action(action)
                    except queue.Empty:
                        break
                
                await asyncio.sleep(1)  # 控制间隔
                
            except Exception as e:
                print(f"  ❌ 控制循环出错: {e}")
                await asyncio.sleep(3)
    
    async def _execute_control_action(self, action: Dict[str, Any]):
        """执行控制动作"""
        action_type = action.get("action", "unknown")
        device_id = action.get("device_id", "auto")
        parameters = action.get("parameters", {})
        
        print(f"🔧 执行控制: {action_type} on {device_id}")
        
        # 创建动作记录
        hardware_action = HardwareAction(
            action_type=action_type,
            device_id=str(device_id),
            parameters=parameters,
            timestamp=datetime.now()
        )
        
        # 根据动作类型执行相应的控制
        success = False
        outcome = None
        
        try:
            if action_type == "cool_down":
                success, outcome = await self._control_cool_down(device_id, parameters)
            elif action_type == "optimize_power":
                success, outcome = await self._control_optimize_power(device_id, parameters)
            elif action_type == "adjust_spectrum":
                success, outcome = await self._control_adjust_spectrum(parameters)
            elif action_type == "camera_capture":
                success, outcome = await self._control_camera_capture(parameters)
            elif action_type == "bluetooth_command":
                success, outcome = await self._control_bluetooth_command(device_id, parameters)
            elif action_type == "infrared_command":
                success, outcome = await self._control_infrared_command(device_id, parameters)
            else:
                # 默认控制逻辑
                success, outcome = await self._execute_default_control(action_type, device_id, parameters)
            
            # 记录学习数据
            self.learning_engine.record_action(hardware_action, success, outcome)
            
            # 更新学习状态
            if success:
                self.learning_state.successful_controls += 1
            else:
                self.learning_state.failed_controls += 1
            
            # 更新设备状态
            if device_id in self.device_states:
                self.device_states[device_id]["last_control"] = datetime.now().isoformat()
                self.device_states[device_id]["control_count"] += 1
                if success:
                    self.device_states[device_id]["success_count"] += 1
            
            print(f"  {'✅' if success else '❌'} 控制执行{'成功' if success else '失败'}")
            
        except Exception as e:
            print(f"  ❌ 控制执行异常: {e}")
            self.learning_engine.record_action(hardware_action, False, {"error": str(e)})
    
    async def _control_cool_down(self, device_id: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict]:
        """控制降温"""
        try:
            intensity = parameters.get("intensity", 0.5)
            
            # 使用光谱控制器降低热量产生
            if self.controllers["spectrum"].is_connected:
                # 降低远红外强度
                await advanced_features.dynamic_far_red_control(
                    temperature=25 - intensity * 5,
                    humidity=60
                )
                return True, {"action": "reduced_far_red", "intensity": intensity}
            
            return False, {"error": "光谱控制器未连接"}
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _control_optimize_power(self, device_id: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict]:
        """控制功耗优化"""
        try:
            target_efficiency = parameters.get("target_efficiency", 0.9)
            
            # 启用节能模式
            if self.controllers["spectrum"].is_connected:
                success = await advanced_features.energy_saving_mode(enable=True)
                return success, {"action": "energy_saving_mode", "target_efficiency": target_efficiency}
            
            return False, {"error": "光谱控制器未连接"}
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _control_adjust_spectrum(self, parameters: Dict[str, Any]) -> Tuple[bool, Dict]:
        """调整光谱"""
        try:
            recipe = parameters.get("recipe", {
                "uv_380nm": 0.05,
                "far_red_720nm": 0.1,
                "white_light": 0.7,
                "red_660nm": 0.15
            })
            
            if self.controllers["spectrum"].is_connected:
                success = await self.controllers["spectrum"].set_spectrum_recipe(recipe)
                return success, {"recipe": recipe}
            
            return False, {"error": "光谱控制器未连接"}
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _control_camera_capture(self, parameters: Dict[str, Any]) -> Tuple[bool, Dict]:
        """控制摄像头捕获"""
        try:
            camera_index = parameters.get("camera_index", 0)
            
            controller = self.controllers["camera"]
            result = controller.open_camera(camera_index)
            
            if result["success"]:
                # 拍摄照片
                frame = controller.take_photo()
                if frame is not None:
                    # 保存照片
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"capture_{timestamp}.jpg"
                    import cv2
                    cv2.imwrite(filename, frame)
                    
                    controller.close_camera()
                    return True, {"filename": filename, "frame_shape": frame.shape}
            
            return False, {"error": "摄像头操作失败"}
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _control_bluetooth_command(self, device_id: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict]:
        """执行蓝牙命令"""
        try:
            controller = self.controllers["bluetooth"]
            
            # 查找设备
            device = None
            for d in self.devices:
                if str(d["id"]) == device_id and d.get("connection_type") == "bluetooth":
                    device = d
                    break
            
            if device:
                # 连接设备
                if not controller.is_connected:
                    conn_result = controller.connect({
                        "bluetooth_address": device.get("connection_details", {}).get("bluetooth_address", ""),
                        "bluetooth_version": device.get("connection_details", {}).get("bluetooth_version", "5.0")
                    })
                    
                    if not conn_result["success"]:
                        return False, {"error": "连接失败"}
                
                # 发送命令
                cmd_result = controller.send_command(parameters)
                return cmd_result["success"], cmd_result
            
            return False, {"error": "设备未找到"}
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _control_infrared_command(self, device_id: str, parameters: Dict[str, Any]) -> Tuple[bool, Dict]:
        """执行红外命令"""
        try:
            controller = self.controllers["infrared"]
            
            # 查找设备
            device = None
            for d in self.devices:
                if str(d["id"]) == device_id and d.get("connection_type") == "infrared":
                    device = d
                    break
            
            if device:
                # 连接设备
                if not controller.is_connected:
                    conn_result = controller.connect({
                        "channel": device.get("connection_details", {}).get("infrared_channel", 1),
                        "range": device.get("connection_details", {}).get("infrared_range", 10)
                    })
                    
                    if not conn_result["success"]:
                        return False, {"error": "连接失败"}
                
                # 发送命令
                cmd_result = controller.send_command(parameters)
                return cmd_result["success"], cmd_result
            
            return False, {"error": "设备未找到"}
        except Exception as e:
            return False, {"error": str(e)}
    
    async def _execute_default_control(self, action_type: str, device_id: str, 
                                       parameters: Dict[str, Any]) -> Tuple[bool, Dict]:
        """执行默认控制"""
        # 使用学习引擎优化参数
        optimal_params = self.learning_engine.learn_optimal_parameters(device_id, action_type)
        if optimal_params:
            # 合并最优参数
            merged_params = {**optimal_params, **parameters}
            parameters = merged_params
        
        # 模拟控制执行
        await asyncio.sleep(0.1)
        return True, {"action": action_type, "optimized": bool(optimal_params)}
    
    async def _learning_loop(self):
        """学习循环"""
        while self.is_running:
            try:
                await self._perform_learning()
                await asyncio.sleep(10)  # 学习间隔
            except Exception as e:
                print(f"  ❌ 学习循环出错: {e}")
                await asyncio.sleep(30)
    
    async def _perform_learning(self):
        """执行学习"""
        print("🎓 执行学习周期...")
        
        # 1. 从学习引擎获取优化建议
        learning_summary = self.learning_engine.get_learning_summary()
        
        # 2. 优化各设备的控制参数
        for device in self.devices:
            device_id = str(device["id"])
            
            # 学习该设备的最优参数
            for action_type in ["cool_down", "optimize_power", "adjust_spectrum"]:
                optimal_params = self.learning_engine.learn_optimal_parameters(device_id, action_type)
                if optimal_params:
                    print(f"  📊 设备 {device_id} 的 {action_type} 最优参数: {optimal_params}")
        
        # 3. 获取硬件数据用于训练
        recent_data = await self.hardware_data_collector.get_recent_data(50)
        
        # 4. 更新学习状态
        self.learning_state.learning_cycles += 1
        self.learning_state.last_update = datetime.now().isoformat()
        
        # 计算性能分数
        total_controls = self.learning_state.successful_controls + self.learning_state.failed_controls
        if total_controls > 0:
            self.learning_state.performance_score = self.learning_state.successful_controls / total_controls
        
        print(f"  ✅ 学习完成 - 周期: {self.learning_state.learning_cycles}, "
              f"性能分数: {self.learning_state.performance_score:.2%}")
    
    async def _get_hardware_status(self) -> Dict[str, Any]:
        """获取硬件状态"""
        status = {
            "total_devices": len(self.devices),
            "connected_devices": len([d for d in self.devices if d.get("connected", False)]),
            "device_types": {},
            "connection_types": {},
            "device_states": self.device_states
        }
        
        for device in self.devices:
            device_type = device.get("type", "unknown")
            if device_type in status["device_types"]:
                status["device_types"][device_type] += 1
            else:
                status["device_types"][device_type] = 1
            
            conn_type = device.get("connection_type", "unknown")
            if conn_type in status["connection_types"]:
                status["connection_types"][conn_type] += 1
            else:
                status["connection_types"][conn_type] = 1
        
        return status
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "is_running": self.is_running,
            "control_strategy": self.control_strategy.value,
            "devices": {
                "total": len(self.devices),
                "connected": len([d for d in self.devices if d.get("connected", False)])
            },
            "learning": self.learning_state.to_dict(),
            "learning_engine": self.learning_engine.get_learning_summary(),
            "queues": {
                "decisions": self.decision_queue.qsize(),
                "controls": self.control_queue.qsize()
            }
        }
    
    async def manual_control(self, device_id: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """手动控制接口"""
        control_action = {
            "action": action,
            "device_id": device_id,
            "parameters": parameters,
            "priority": "high"
        }
        self.control_queue.put(control_action)
        
        return {
            "success": True,
            "message": f"手动控制命令已发送: {action}",
            "device_id": device_id,
            "queued": True
        }
    
    async def run_demo(self, duration: int = 60):
        """运行演示"""
        print(f"\n🎮 启动自动学习控制演示 (持续 {duration} 秒)...")
        print("=" * 60)
        
        start_time = time.time()
        cycle = 0
        
        while time.time() - start_time < duration and self.is_running:
            cycle += 1
            print(f"\n{'='*20} 演示周期 {cycle} {'='*20}")
            
            # 显示系统状态
            status = self.get_system_status()
            print(f"📊 系统状态:")
            print(f"   设备: {status['devices']['connected']}/{status['devices']['total']} 在线")
            print(f"   决策: {status['learning']['total_decisions']}, "
                  f"成功: {status['learning']['successful_controls']}")
            print(f"   学习周期: {status['learning']['learning_cycles']}, "
                  f"性能: {status['learning']['performance_score']:.2%}")
            
            # 模拟一些手动控制
            if cycle % 5 == 0 and self.devices:
                device = self.devices[cycle % len(self.devices)]
                await self.manual_control(
                    str(device["id"]),
                    "status_check",
                    {"timestamp": datetime.now().isoformat()}
                )
            
            await asyncio.sleep(5)
        
        print(f"\n✅ 演示完成 - 共执行 {cycle} 个周期")
    
    async def cleanup(self):
        """清理资源"""
        print("\n🧹 清理系统资源...")
        
        self.is_running = False
        
        # 取消所有任务
        for task in self.tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # 停止硬件数据收集
        await self.hardware_data_collector.stop_collection()
        
        # 清理智能体
        await self.agent_manager.cleanup()
        
        # 断开所有控制器
        for name, controller in self.controllers.items():
            if hasattr(controller, 'disconnect'):
                try:
                    if name == "spectrum":
                        await controller.disconnect()
                    else:
                        controller.disconnect()
                except:
                    pass
        
        print("✅ 系统已清理")


async def main():
    """主函数"""
    print("🤖 自动学习控制本地硬件系统")
    print("=" * 60)
    
    # 创建系统实例
    system = AutoLearnHardwareControlSystem()
    
    try:
        # 初始化系统
        await system.initialize_system()
        
        # 运行演示
        await system.run_demo(duration=60)
        
        # 显示最终状态
        print("\n" + "=" * 60)
        print("📊 最终系统状态:")
        final_status = system.get_system_status()
        print(json.dumps(final_status, indent=2, ensure_ascii=False))
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 系统运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        await system.cleanup()
    
    print("\n🎯 自动学习硬件控制系统运行完成!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
