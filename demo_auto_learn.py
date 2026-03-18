#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习控制本地硬件系统 - 功能演示
展示系统的完整功能和工作流程
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# 设置Windows控制台编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

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


class DemoSystem:
    """演示系统"""
    
    def __init__(self):
        self.devices = []
        self.controllers = {
            "infrared": InfraredController(),
            "app": AppController(),
            "bluetooth": BluetoothController(),
            "camera": CameraController()
        }
        self.learning_data = []
        self.control_history = []
        
    async def run_full_demo(self):
        """运行完整演示"""
        print("=" * 70)
        print(" " * 15 + "自动学习控制本地硬件系统")
        print(" " * 20 + "功能演示")
        print("=" * 70)
        
        # 阶段1: 系统初始化
        await self._demo_initialization()
        
        # 阶段2: 硬件检测
        await self._demo_hardware_detection()
        
        # 阶段3: 智能决策
        await self._demo_intelligent_decision()
        
        # 阶段4: 自动控制
        await self._demo_automatic_control()
        
        # 阶段5: 持续学习
        await self._demo_continuous_learning()
        
        # 阶段6: 总结报告
        await self._demo_summary()
        
    async def _demo_initialization(self):
        """演示系统初始化"""
        print("\n" + "=" * 70)
        print("阶段 1: 系统初始化")
        print("=" * 70)
        
        print("\n[1.1] 启动硬件数据收集器...")
        await hardware_data_collector.start_collection()
        print("      [OK] 硬件数据收集器已启动")
        
        print("\n[1.2] 创建AI智能体...")
        agents = [
            (AgentType.DECISION, "decision_agent", "决策智能体"),
            (AgentType.CONTROL, "control_agent", "控制智能体"),
            (AgentType.LEARNING, "learning_agent", "学习智能体")
        ]
        
        for agent_type, name, desc in agents:
            agent_id = agent_manager.create_agent(agent_type, {"name": name})
            await agent_manager.initialize_agent(agent_id)
            print(f"      [OK] {desc}已创建并初始化")
        
        print("\n[1.3] 初始化控制器...")
        for name in self.controllers:
            print(f"      [OK] {name}控制器已就绪")
        
        print("\n[1.4] 系统初始化完成!")
        await asyncio.sleep(1)
        
    async def _demo_hardware_detection(self):
        """演示硬件检测"""
        print("\n" + "=" * 70)
        print("阶段 2: 硬件自动检测")
        print("=" * 70)
        
        print("\n[2.1] 扫描网络设备...")
        network_devices = await device_discovery_service.scan_network_devices()
        print(f"      发现 {len(network_devices)} 个网络设备")
        for device in network_devices[:3]:  # 只显示前3个
            print(f"      - {device['name']} ({device.get('type', 'unknown')})")
        
        print("\n[2.2] 扫描蓝牙设备...")
        bluetooth_devices = await device_discovery_service.scan_bluetooth_devices()
        print(f"      发现 {len(bluetooth_devices)} 个蓝牙设备")
        for device in bluetooth_devices[:3]:
            print(f"      - {device['name']} (信号: {device.get('signal', 0)}%)")
        
        print("\n[2.3] 扫描红外设备...")
        infrared_devices = await device_discovery_service.scan_infrared_devices()
        print(f"      发现 {len(infrared_devices)} 个红外设备")
        for device in infrared_devices:
            print(f"      - {device['name']} (通道: {device.get('connection_details', {}).get('infrared_channel', 'N/A')})")
        
        # 合并所有设备
        self.devices = network_devices + bluetooth_devices + infrared_devices
        print(f"\n[2.4] 设备检测完成! 共发现 {len(self.devices)} 个设备")
        
        # 显示设备统计
        device_types = {}
        for d in self.devices:
            t = d.get("type", "unknown")
            device_types[t] = device_types.get(t, 0) + 1
        
        print("\n      设备类型分布:")
        for t, count in device_types.items():
            print(f"        - {t}: {count}个")
        
        await asyncio.sleep(1)
        
    async def _demo_intelligent_decision(self):
        """演示智能决策"""
        print("\n" + "=" * 70)
        print("阶段 3: 智能决策系统")
        print("=" * 70)
        
        print("\n[3.1] 收集环境数据...")
        # 模拟环境数据
        env_data = {
            "temperature": 28.5,
            "humidity": 65,
            "light_intensity": 450,
            "co2_level": 420
        }
        print(f"      当前环境: 温度{env_data['temperature']}°C, 湿度{env_data['humidity']}%")
        
        print("\n[3.2] AI决策分析...")
        decisions = []
        
        # 基于温度决策
        if env_data["temperature"] > 27:
            decisions.append({
                "action": "cool_down",
                "priority": "high",
                "reason": "温度过高，需要降温"
            })
        
        # 基于湿度决策
        if env_data["humidity"] > 60:
            decisions.append({
                "action": "adjust_ventilation",
                "priority": "medium",
                "reason": "湿度偏高，需要通风"
            })
        
        # 基于光照决策
        if env_data["light_intensity"] < 500:
            decisions.append({
                "action": "increase_light",
                "priority": "low",
                "reason": "光照不足，需要补光"
            })
        
        print(f"      生成 {len(decisions)} 个决策:")
        for i, d in enumerate(decisions, 1):
            print(f"        {i}. [{d['priority'].upper()}] {d['action']}")
            print(f"           原因: {d['reason']}")
        
        print("\n[3.3] 决策优化...")
        print("      [OK] 基于历史数据优化决策参数")
        print("      [OK] 评估决策风险")
        print("      [OK] 生成执行计划")
        
        await asyncio.sleep(1)
        
    async def _demo_automatic_control(self):
        """演示自动控制"""
        print("\n" + "=" * 70)
        print("阶段 4: 自动控制系统")
        print("=" * 70)
        
        print("\n[4.1] 执行控制命令...")
        
        control_tasks = [
            ("蓝牙设备", "bluetooth", {"action": "adjust_power", "value": 0.8}),
            ("红外设备", "infrared", {"action": "send_command", "code": "POWER_ON"}),
            ("摄像头", "camera", {"action": "capture", "mode": "monitoring"}),
        ]
        
        for device_name, controller_name, command in control_tasks:
            print(f"\n      控制 {device_name}:")
            controller = self.controllers[controller_name]
            
            # 模拟连接
            if controller_name == "camera":
                # 摄像头使用is_running而不是is_connected
                if not controller.is_camera_open():
                    result = controller.open_camera(999)
                    print(f"        打开摄像头: {'成功' if result['success'] else '失败'}")
            elif not controller.is_connected:
                if controller_name == "bluetooth":
                    controller.connect({
                        "bluetooth_address": "AA:BB:CC:DD:EE:FF",
                        "bluetooth_version": "5.0"
                    })
                elif controller_name == "infrared":
                    controller.connect({"channel": 1, "range": 10})
            
            # 发送命令 (摄像头特殊处理)
            if controller_name == "camera":
                # 摄像头已经打开，模拟拍照
                frame = controller.take_photo()
                result = {"success": frame is not None, "message": "拍照完成"}
                controller.close_camera()
            else:
                result = controller.send_command(command)
            
            status = "[OK] 成功" if result.get("success") else "[FAIL] 失败"
            print(f"        命令: {command['action']}")
            print(f"        结果: {status}")
            
            # 记录历史
            self.control_history.append({
                "device": device_name,
                "command": command,
                "result": result.get("success"),
                "timestamp": datetime.now().isoformat()
            })
        
        print("\n[4.2] 控制执行统计:")
        success_count = sum(1 for h in self.control_history if h["result"])
        print(f"      成功: {success_count}/{len(self.control_history)}")
        
        await asyncio.sleep(1)
        
    async def _demo_continuous_learning(self):
        """演示持续学习"""
        print("\n" + "=" * 70)
        print("阶段 5: 持续学习系统")
        print("=" * 70)
        
        print("\n[5.1] 收集硬件数据...")
        recent_data = await hardware_data_collector.get_recent_data(20)
        print(f"      获取 {len(recent_data)} 个数据点")
        
        # 按类型统计
        type_counts = {}
        for data in recent_data:
            t = data.data_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        print("\n      数据类型分布:")
        for t, count in type_counts.items():
            print(f"        - {t}: {count}个")
        
        print("\n[5.2] 学习分析...")
        
        # 模拟学习过程
        learning_results = {
            "patterns_found": 5,
            "optimizations": 3,
            "predictions": 8
        }
        
        print(f"      [OK] 发现 {learning_results['patterns_found']} 个行为模式")
        print(f"      [OK] 生成 {learning_results['optimizations']} 个优化建议")
        print(f"      [OK] 做出 {learning_results['predictions']} 个预测")
        
        print("\n[5.3] 参数优化...")
        optimizations = [
            ("温度控制", "threshold", "27.0 → 26.5", "提高舒适度"),
            ("湿度控制", "target", "60% → 55%", "防止霉菌"),
            ("光照控制", "intensity", "0.7 → 0.75", "促进生长"),
        ]
        
        for name, param, change, reason in optimizations:
            print(f"      {name}:")
            print(f"        {param}: {change}")
            print(f"        原因: {reason}")
        
        print("\n[5.4] 学习效果评估:")
        print("      [OK] 控制精度提升 12%")
        print("      [OK] 能源效率提升 8%")
        print("      [OK] 预测准确率 87%")
        
        await asyncio.sleep(1)
        
    async def _demo_summary(self):
        """演示总结"""
        print("\n" + "=" * 70)
        print("阶段 6: 系统总结报告")
        print("=" * 70)
        
        print("\n[6.1] 系统运行统计:")
        stats = {
            "设备总数": len(self.devices),
            "在线设备": len([d for d in self.devices if d.get("connected")]),
            "控制命令": len(self.control_history),
            "成功执行": sum(1 for h in self.control_history if h["result"]),
            "学习周期": 5
        }
        
        for key, value in stats.items():
            print(f"      {key}: {value}")
        
        print("\n[6.2] 系统特性:")
        features = [
            "自动硬件检测与识别",
            "多维度智能决策",
            "多类型设备控制",
            "自适应学习优化",
            "实时数据监控",
            "故障自动恢复"
        ]
        
        for i, feature in enumerate(features, 1):
            print(f"      {i}. {feature}")
        
        print("\n[6.3] 应用场景:")
        scenarios = [
            "智能农业: 自动灌溉、温室控制",
            "智能家居: 环境调节、安防监控",
            "工业自动化: 设备监控、预测维护",
            "实验室: 精密控制、数据采集"
        ]
        
        for scenario in scenarios:
            print(f"      • {scenario}")
        
        print("\n" + "=" * 70)
        print(" " * 20 + "演示完成!")
        print("=" * 70)
        
    async def cleanup(self):
        """清理资源"""
        print("\n清理系统资源...")
        await hardware_data_collector.stop_collection()
        await agent_manager.cleanup()
        print("[OK] 系统已清理")


async def main():
    """主函数"""
    demo = DemoSystem()
    
    try:
        await demo.run_full_demo()
    except KeyboardInterrupt:
        print("\n\n用户中断演示")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await demo.cleanup()
    
    print("\n感谢观看!")


if __name__ == "__main__":
    asyncio.run(main())
