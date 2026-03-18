#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习控制本地硬件系统 - 简化版
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.core.agent_manager import agent_manager, AgentType
from backend.src.core.services.device_discovery_service import device_discovery_service
from backend.src.core.services.hardware_data_collector import hardware_data_collector
from backend.src.core.services.connection_controller import InfraredController, AppController, BluetoothController
from backend.src.core.services.camera_controller import CameraController


class SimpleAutoLearnSystem:
    """简化版自动学习系统"""
    
    def __init__(self):
        self.devices = []
        self.controllers = {
            "infrared": InfraredController(),
            "app": AppController(),
            "bluetooth": BluetoothController(),
            "camera": CameraController()
        }
        self.stats = {
            "decisions": 0,
            "controls": 0,
            "success": 0,
            "learning_cycles": 0
        }
    
    async def initialize(self):
        """初始化系统"""
        print("初始化自动学习控制系统...")
        
        # 扫描设备
        print("扫描本地硬件设备...")
        self.devices = await device_discovery_service.scan_all_devices()
        print(f"发现 {len(self.devices)} 个设备")
        
        # 显示设备列表
        for device in self.devices:
            print(f"  [{device['id']}] {device['name']} ({device.get('type', 'unknown')}) - "
                  f"{'在线' if device.get('connected') else '离线'}")
        
        # 启动数据收集
        await hardware_data_collector.start_collection()
        print("硬件数据收集已启动")
        
        # 创建智能体
        await self._create_agents()
        
        print("系统初始化完成")
        return True
    
    async def _create_agents(self):
        """创建智能体"""
        print("创建智能体...")
        
        agents = [
            (AgentType.DECISION, "decision_agent"),
            (AgentType.CONTROL, "control_agent"),
            (AgentType.LEARNING, "learning_agent")
        ]
        
        for agent_type, name in agents:
            agent_id = agent_manager.create_agent(agent_type, {"name": name})
            await agent_manager.initialize_agent(agent_id)
            print(f"  创建智能体: {name}")
    
    async def run_cycle(self):
        """运行一个控制周期"""
        print("\n执行控制周期...")
        
        # 获取硬件状态
        status = await self._get_hardware_status()
        print(f"设备状态: {status['connected']}/{status['total']} 在线")
        
        # 对每个连接的设备执行控制
        for device in self.devices:
            if device.get("connected"):
                await self._control_device(device)
        
        # 执行学习
        await self._learn()
        
        self.stats["decisions"] += 1
        
        return True
    
    async def _control_device(self, device):
        """控制单个设备"""
        device_id = device["id"]
        device_type = device.get("type", "unknown")
        conn_type = device.get("connection_type", "unknown")
        
        print(f"  控制设备 [{device_id}] {device['name']}")
        
        # 根据连接类型选择控制器
        if conn_type == "bluetooth":
            controller = self.controllers["bluetooth"]
            # 先建立连接
            if not controller.is_connected:
                conn_details = device.get("connection_details", {})
                controller.connect({
                    "bluetooth_address": conn_details.get("bluetooth_address", "00:00:00:00:00:00"),
                    "bluetooth_version": conn_details.get("bluetooth_version", "5.0")
                })
            result = controller.send_command({"action": "status_check", "device_id": device_id})
        elif conn_type == "infrared":
            controller = self.controllers["infrared"]
            # 先建立连接
            if not controller.is_connected:
                conn_details = device.get("connection_details", {})
                controller.connect({
                    "channel": conn_details.get("infrared_channel", 1),
                    "range": conn_details.get("infrared_range", 10)
                })
            result = controller.send_command({"action": "status_check", "device_id": device_id})
        elif device_type == "camera":
            controller = self.controllers["camera"]
            result = controller.open_camera(999)  # 使用模拟摄像头
            if result["success"]:
                controller.close_camera()
        else:
            result = {"success": True, "message": "默认控制"}
        
        self.stats["controls"] += 1
        if result.get("success"):
            self.stats["success"] += 1
        
        print(f"    结果: {'成功' if result.get('success') else '失败'}")
    
    async def _learn(self):
        """执行学习"""
        print("  执行学习...")
        
        # 获取最近的数据
        recent_data = await hardware_data_collector.get_recent_data(10)
        
        if recent_data:
            print(f"    学习 {len(recent_data)} 个数据点")
            self.stats["learning_cycles"] += 1
        
        return True
    
    async def _get_hardware_status(self):
        """获取硬件状态"""
        return {
            "total": len(self.devices),
            "connected": len([d for d in self.devices if d.get("connected", False)])
        }
    
    def get_stats(self):
        """获取统计信息"""
        return self.stats
    
    async def cleanup(self):
        """清理资源"""
        print("\n清理系统资源...")
        
        await hardware_data_collector.stop_collection()
        await agent_manager.cleanup()
        
        print("系统已清理")


async def main():
    """主函数"""
    print("=" * 60)
    print("自动学习控制本地硬件系统")
    print("=" * 60)
    
    system = SimpleAutoLearnSystem()
    
    try:
        # 初始化
        await system.initialize()
        
        # 运行5个周期
        print("\n开始运行控制周期...")
        for i in range(5):
            print(f"\n{'='*20} 周期 {i+1}/5 {'='*20}")
            await system.run_cycle()
            await asyncio.sleep(2)
        
        # 显示统计
        print("\n" + "=" * 60)
        print("运行统计:")
        stats = system.get_stats()
        print(f"  决策次数: {stats['decisions']}")
        print(f"  控制次数: {stats['controls']}")
        print(f"  成功次数: {stats['success']}")
        print(f"  学习周期: {stats['learning_cycles']}")
        if stats['controls'] > 0:
            print(f"  成功率: {stats['success']/stats['controls']*100:.1f}%")
        
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await system.cleanup()
    
    print("\n系统运行完成!")


if __name__ == "__main__":
    asyncio.run(main())
