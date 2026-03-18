"""
设备管理技能 - 为边缘计算智能体提供设备连接和控制功能
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import logging
from enum import Enum
import random

logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """设备类型枚举"""
    SENSOR = "传感器"
    ACTUATOR = "执行器"
    CAMERA = "摄像头"
    DRONE = "无人机"
    IRRIGATION = "灌溉设备"
    ROBOT = "农业机器人"

class DeviceStatus(Enum):
    """设备状态枚举"""
    ONLINE = "在线"
    OFFLINE = "离线"
    ACTIVE = "工作中"
    IDLE = "空闲"
    ERROR = "故障"
    MAINTENANCE = "维护中"

class DeviceSkill:
    """设备管理技能"""
    
    def __init__(self, mqtt_broker: Optional[str] = None):
        """
        初始化设备管理技能
        
        Args:
            mqtt_broker: MQTT代理地址
        """
        self.mqtt_broker = mqtt_broker or "mqtt://localhost:1883"
        self.devices = {}  # 设备注册表
        self.device_data = {}  # 设备数据缓存
        self.callbacks = {}  # 回调函数注册
        
        # 模拟设备初始化
        self._initialize_mock_devices()
    
    def _initialize_mock_devices(self):
        """初始化模拟设备"""
        mock_devices = [
            {
                "device_id": "sensor_temp_001",
                "name": "温度传感器",
                "type": DeviceType.SENSOR,
                "location": "大棚A区",
                "coordinates": (31.2304, 121.4737),
                "capabilities": ["temperature", "humidity"],
                "status": DeviceStatus.ONLINE
            },
            {
                "device_id": "sensor_soil_001",
                "name": "土壤传感器",
                "type": DeviceType.SENSOR,
                "location": "大棚A区",
                "coordinates": (31.2305, 121.4738),
                "capabilities": ["soil_moisture", "soil_temperature", "soil_ph"],
                "status": DeviceStatus.ONLINE
            },
            {
                "device_id": "actuator_valve_001",
                "name": "灌溉阀门",
                "type": DeviceType.ACTUATOR,
                "location": "大棚A区",
                "coordinates": (31.2306, 121.4739),
                "capabilities": ["open", "close", "set_flow_rate"],
                "status": DeviceStatus.IDLE
            },
            {
                "device_id": "camera_field_001",
                "name": "田间摄像头",
                "type": DeviceType.CAMERA,
                "location": "大棚A区",
                "coordinates": (31.2307, 121.4740),
                "capabilities": ["capture_image", "record_video", "object_detection"],
                "status": DeviceStatus.ONLINE
            },
            {
                "device_id": "drone_spray_001",
                "name": "植保无人机",
                "type": DeviceType.DRONE,
                "location": "机库",
                "coordinates": (31.2308, 121.4741),
                "capabilities": ["autonomous_flight", "spraying", "mapping"],
                "status": DeviceStatus.IDLE
            }
        ]
        
        for device_info in mock_devices:
            self.devices[device_info["device_id"]] = device_info
    
    async def discover_devices(self, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        发现设备
        
        Args:
            location: 位置筛选（可选）
        
        Returns:
            设备列表
        """
        await asyncio.sleep(0.5)  # 模拟网络延迟
        
        discovered = []
        for device_id, device_info in self.devices.items():
            if location and device_info["location"] != location:
                continue
            
            # 模拟设备发现
            device_status = self._get_device_status(device_id)
            device_info_copy = device_info.copy()
            device_info_copy["status"] = device_status.value
            device_info_copy["last_seen"] = datetime.now().isoformat()
            
            discovered.append(device_info_copy)
        
        logger.info(f"发现 {len(discovered)} 个设备")
        return discovered
    
    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """
        获取设备状态
        
        Args:
            device_id: 设备ID
        
        Returns:
            设备状态信息
        """
        if device_id not in self.devices:
            return {
                "error": f"设备 {device_id} 未找到",
                "device_id": device_id
            }
        
        device_info = self.devices[device_id]
        status = self._get_device_status(device_id)
        
        # 获取设备数据
        device_data = self.device_data.get(device_id, {})
        
        return {
            "device_id": device_id,
            "name": device_info["name"],
            "type": device_info["type"].value,
            "location": device_info["location"],
            "status": status.value,
            "last_update": datetime.now().isoformat(),
            "data": device_data,
            "battery_level": random.randint(20, 100) if device_info["type"] in [DeviceType.DRONE, DeviceType.ROBOT] else None,
            "signal_strength": random.randint(60, 100)
        }
    
    async def control_device(self, device_id: str, command: str, 
                           parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        控制设备
        
        Args:
            device_id: 设备ID
            command: 控制命令
            parameters: 命令参数
        
        Returns:
            控制结果
        """
        if device_id not in self.devices:
            return {
                "success": False,
                "error": f"设备 {device_id} 未找到",
                "device_id": device_id
            }
        
        device_info = self.devices[device_id]
        capabilities = device_info["capabilities"]
        
        # 检查设备是否支持该命令
        if command not in capabilities:
            return {
                "success": False,
                "error": f"设备不支持命令: {command}",
                "device_id": device_id,
                "supported_commands": capabilities
            }
        
        # 检查设备状态
        current_status = self._get_device_status(device_id)
        if current_status == DeviceStatus.OFFLINE:
            return {
                "success": False,
                "error": "设备离线",
                "device_id": device_id,
                "status": current_status.value
            }
        elif current_status == DeviceStatus.ERROR:
            return {
                "success": False,
                "error": "设备故障",
                "device_id": device_id,
                "status": current_status.value
            }
        
        # 执行控制命令
        try:
            result = await self._execute_command(device_id, command, parameters or {})
            
            # 更新设备状态
            if command in ["open", "start", "activate"]:
                self._update_device_status(device_id, DeviceStatus.ACTIVE)
            elif command in ["close", "stop", "deactivate"]:
                self._update_device_status(device_id, DeviceStatus.IDLE)
            
            # 触发回调
            await self._trigger_callbacks(device_id, command, result)
            
            return {
                "success": True,
                "device_id": device_id,
                "command": command,
                "parameters": parameters,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"控制设备失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id,
                "command": command
            }
    
    async def read_sensor_data(self, device_id: str, 
                             sensor_type: Optional[str] = None) -> Dict[str, Any]:
        """
        读取传感器数据
        
        Args:
            device_id: 设备ID
            sensor_type: 传感器类型（可选）
        
        Returns:
            传感器数据
        """
        if device_id not in self.devices:
            return {
                "error": f"设备 {device_id} 未找到",
                "device_id": device_id
            }
        
        device_info = self.devices[device_id]
        if device_info["type"] != DeviceType.SENSOR:
            return {
                "error": f"设备 {device_id} 不是传感器",
                "device_id": device_id,
                "type": device_info["type"].value
            }
        
        # 模拟传感器数据读取
        sensor_data = self._generate_sensor_data(device_id, device_info, sensor_type)
        
        # 缓存数据
        self.device_data[device_id] = sensor_data
        
        # 触发数据回调
        await self._trigger_data_callbacks(device_id, sensor_data)
        
        return {
            "device_id": device_id,
            "name": device_info["name"],
            "location": device_info["location"],
            "timestamp": datetime.now().isoformat(),
            "data": sensor_data,
            "data_quality": "良好" if random.random() > 0.1 else "一般"
        }
    
    async def schedule_task(self, device_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        调度设备任务
        
        Args:
            device_id: 设备ID
            task: 任务定义
        
        Returns:
            调度结果
        """
        if device_id not in self.devices:
            return {
                "success": False,
                "error": f"设备 {device_id} 未找到"
            }
        
        # 验证任务
        validation_result = self._validate_task(device_id, task)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": "任务验证失败",
                "details": validation_result
            }
        
        # 创建任务ID
        task_id = f"task_{device_id}_{int(datetime.now().timestamp())}"
        
        # 模拟任务调度
        scheduled_time = task.get("scheduled_time", datetime.now().isoformat())
        
        # 这里实际应该将任务加入调度队列
        # 简化处理：立即执行或记录调度
        
        return {
            "success": True,
            "task_id": task_id,
            "device_id": device_id,
            "task_type": task.get("type", "unknown"),
            "scheduled_time": scheduled_time,
            "estimated_duration": task.get("estimated_duration", "未知"),
            "priority": task.get("priority", "normal")
        }
    
    def register_callback(self, device_id: str, event_type: str, 
                         callback: Callable) -> bool:
        """
        注册回调函数
        
        Args:
            device_id: 设备ID
            event_type: 事件类型
            callback: 回调函数
        
        Returns:
            是否注册成功
        """
        key = f"{device_id}_{event_type}"
        self.callbacks[key] = callback
        logger.info(f"回调函数注册: {key}")
        return True
    
    def _get_device_status(self, device_id: str) -> DeviceStatus:
        """获取设备状态（模拟）"""
        # 在实际系统中，这里应该从设备获取实时状态
        # 这里使用模拟状态
        
        if device_id not in self.devices:
            return DeviceStatus.OFFLINE
        
        # 模拟状态变化
        if random.random() < 0.05:  # 5%概率离线
            return DeviceStatus.OFFLINE
        elif random.random() < 0.02:  # 2%概率故障
            return DeviceStatus.ERROR
        
        device_info = self.devices[device_id]
        return device_info.get("status", DeviceStatus.ONLINE)
    
    def _update_device_status(self, device_id: str, status: DeviceStatus):
        """更新设备状态"""
        if device_id in self.devices:
            self.devices[device_id]["status"] = status
    
    async def _execute_command(self, device_id: str, command: str, 
                             parameters: Dict) -> Dict[str, Any]:
        """执行设备命令（模拟）"""
        await asyncio.sleep(0.3)  # 模拟执行时间
        
        device_info = self.devices[device_id]
        device_type = device_info["type"]
        
        # 根据设备类型和命令生成结果
        if device_type == DeviceType.ACTUATOR:
            if command == "open":
                return {"valve_position": "open", "flow_rate": parameters.get("flow_rate", 10)}
            elif command == "close":
                return {"valve_position": "closed", "flow_rate": 0}
            elif command == "set_flow_rate":
                flow_rate = parameters.get("flow_rate", 5)
                return {"flow_rate": flow_rate, "status": "adjusted"}
        
        elif device_type == DeviceType.DRONE:
            if command == "autonomous_flight":
                return {"flight_mode": "autonomous", "target_area": parameters.get("area", "field")}
            elif command == "spraying":
                return {"spraying": True, "chemical": parameters.get("chemical", "water")}
        
        elif device_type == DeviceType.CAMERA:
            if command == "capture_image":
                return {"image_captured": True, "resolution": parameters.get("resolution", "1080p")}
            elif command == "record_video":
                return {"recording": True, "duration": parameters.get("duration", 60)}
        
        # 默认返回
        return {
            "command_executed": command,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_sensor_data(self, device_id: str, device_info: Dict, 
                            sensor_type: Optional[str]) -> Dict[str, Any]:
        """生成传感器数据（模拟）"""
        capabilities = device_info["capabilities"]
        data = {}
        
        # 根据设备能力生成数据
        for capability in capabilities:
            if sensor_type and capability != sensor_type:
                continue
            
            if capability == "temperature":
                data["temperature"] = round(20 + random.uniform(-5, 10), 1)
                data["temperature_unit"] = "°C"
            
            elif capability == "humidity":
                data["humidity"] = random.randint(40, 90)
                data["humidity_unit"] = "%"
            
            elif capability == "soil_moisture":
                data["soil_moisture"] = round(random.uniform(10, 40), 1)
                data["soil_moisture_unit"] = "%"
            
            elif capability == "soil_temperature":
                data["soil_temperature"] = round(15 + random.uniform(-5, 10), 1)
                data["soil_temperature_unit"] = "°C"
            
            elif capability == "soil_ph":
                data["soil_ph"] = round(6.0 + random.uniform(-1.5, 1.5), 1)
            
            elif capability == "light_intensity":
                data["light_intensity"] = random.randint(1000, 10000)
                data["light_intensity_unit"] = "lux"
        
        return data
    
    def _validate_task(self, device_id: str, task: Dict) -> Dict[str, Any]:
        """验证任务"""
        device_info = self.devices[device_id]
        capabilities = device_info["capabilities"]
        
        task_type = task.get("type")
        if not task_type:
            return {"valid": False, "reason": "任务类型未指定"}
        
        # 检查设备是否支持该任务类型
        if task_type not in capabilities:
            return {
                "valid": False,
                "reason": f"设备不支持任务类型: {task_type}",
                "supported_types": capabilities
            }
        
        # 检查时间参数
        scheduled_time = task.get("scheduled_time")
        if scheduled_time:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                if scheduled_dt < datetime.now():
                    return {"valid": False, "reason": "计划时间已过"}
            except ValueError:
                return {"valid": False, "reason": "时间格式错误"}
        
        return {"valid": True, "device_capabilities": capabilities}
    
    async def _trigger_callbacks(self, device_id: str, command: str, result: Dict):
        """触发回调函数"""
        event_key = f"{device_id}_command"
        if event_key in self.callbacks:
            try:
                await self.callbacks[event_key](device_id, command, result)
            except Exception as e:
                logger.error(f"回调函数执行失败: {e}")
    
    async def _trigger_data_callbacks(self, device_id: str, data: Dict):
        """触发数据回调"""
        event_key = f"{device_id}_data"
        if event_key in self.callbacks:
            try:
                await self.callbacks[event_key](device_id, data)
            except Exception as e:
                logger.error(f"数据回调函数执行失败: {e}")


# 使用示例
async def example_usage():
    """使用示例"""
    device_skill = DeviceSkill()
    
    # 发现设备
    devices = await device_skill.discover_devices("大棚A区")
    print("发现的设备:", json.dumps(devices, indent=2, ensure_ascii=False))
    
    # 获取设备状态
    status = await device_skill.get_device_status("sensor_temp_001")
    print("\n设备状态:", json.dumps(status, indent=2, ensure_ascii=False))
    
    # 读取传感器数据
    sensor_data = await device_skill.read_sensor_data("sensor_temp_001")
    print("\n传感器数据:", json.dumps(sensor_data, indent=2, ensure_ascii=False))
    
    # 控制设备
    control_result = await device_skill.control_device(
        "actuator_valve_001",
        "open",
        {"flow_rate": 10, "duration": 300}
    )
    print("\n控制结果:", json.dumps(control_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())