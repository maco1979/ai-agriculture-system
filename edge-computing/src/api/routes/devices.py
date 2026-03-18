"""
物联网设备管理API路由
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import asyncio
import json

router = APIRouter(prefix="/api/edge/devices", tags=["物联网设备管理"])


class DeviceBase(BaseModel):
    """设备基础模型"""
    device_id: str = Field(..., description="设备唯一标识符")
    device_name: str = Field(..., description="设备名称")
    device_type: str = Field(..., description="设备类型")
    protocol: str = Field(..., description="通信协议")
    location: Optional[str] = Field(None, description="设备位置")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="设备元数据")


class DeviceCreate(DeviceBase):
    """创建设备模型"""
    pass


class DeviceUpdate(BaseModel):
    """更新设备模型"""
    device_name: Optional[str] = None
    location: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceStatus(BaseModel):
    """设备状态模型"""
    device_id: str
    status: str
    last_seen: str
    signal_strength: Optional[float] = None
    battery_level: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None


class DeviceData(BaseModel):
    """设备数据模型"""
    device_id: str
    timestamp: str
    data: Dict[str, Any]
    quality: Optional[float] = None


class DeviceConnection(BaseModel):
    """设备连接模型"""
    device_id: str
    protocol: str
    status: str
    last_connected: str
    ip_address: Optional[str] = None
    port: Optional[int] = None


# 模拟设备存储
devices_db = [
    {
        "device_id": "sensor-001",
        "device_name": "温度传感器",
        "device_type": "sensor",
        "protocol": "MQTT",
        "location": "温室A区",
        "metadata": {
            "manufacturer": "SensorTech",
            "model": "ST-1000",
            "firmware_version": "1.0.0",
            "battery_type": "Li-Ion"
        }
    },
    {
        "device_id": "actuator-001",
        "device_name": "灌溉控制器",
        "device_type": "actuator",
        "protocol": "HTTP",
        "location": "温室B区",
        "metadata": {
            "manufacturer": "ActuatorCorp",
            "model": "AC-2000",
            "firmware_version": "2.1.0",
            "power_source": "AC 220V"
        }
    },
    {
        "device_id": "camera-001",
        "device_name": "监控摄像头",
        "device_type": "camera",
        "protocol": "WebSocket",
        "location": "农场入口",
        "metadata": {
            "manufacturer": "CamTech",
            "model": "CT-3000",
            "firmware_version": "3.2.0",
            "resolution": "1080p"
        }
    }
]


# 设备状态存储
device_statuses = [
    {
        "device_id": "sensor-001",
        "status": "online",
        "last_seen": "2026-02-04T10:00:00Z",
        "signal_strength": 85.5,
        "battery_level": 75.0
    },
    {
        "device_id": "actuator-001",
        "status": "online",
        "last_seen": "2026-02-04T10:01:00Z",
        "signal_strength": 90.0
    },
    {
        "device_id": "camera-001",
        "status": "offline",
        "last_seen": "2026-02-04T09:30:00Z",
        "signal_strength": 0.0
    }
]


# 设备连接管理
class DeviceConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections[device_id] = websocket
        print(f"设备 {device_id} 已连接")
    
    def disconnect(self, device_id: str):
        if device_id in self.active_connections:
            del self.active_connections[device_id]
            print(f"设备 {device_id} 已断开连接")
    
    async def send_personal_message(self, message: Dict[str, Any], device_id: str):
        if device_id in self.active_connections:
            await self.active_connections[device_id].send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        for device_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"发送消息到设备 {device_id} 失败: {str(e)}")
                self.disconnect(device_id)


device_manager = DeviceConnectionManager()


@router.get("/", response_model=List[DeviceBase])
async def get_devices():
    """获取所有设备列表"""
    return devices_db


@router.get("/{device_id}", response_model=DeviceBase)
async def get_device(device_id: str):
    """获取单个设备信息"""
    device = next((d for d in devices_db if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.post("/", response_model=DeviceBase)
async def create_device(device: DeviceCreate):
    """创建设备"""
    # 检查设备ID是否已存在
    if any(d["device_id"] == device.device_id for d in devices_db):
        raise HTTPException(status_code=400, detail="设备ID已存在")
    
    # 创建设备
    new_device = device.model_dump()
    devices_db.append(new_device)
    
    # 初始化设备状态
    new_status = {
        "device_id": device.device_id,
        "status": "offline",
        "last_seen": "",
        "signal_strength": 0.0
    }
    device_statuses.append(new_status)
    
    return new_device


@router.put("/{device_id}", response_model=DeviceBase)
async def update_device(device_id: str, device_update: DeviceUpdate):
    """更新设备信息"""
    device_index = next((i for i, d in enumerate(devices_db) if d["device_id"] == device_id), None)
    if device_index is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 更新设备信息
    update_data = device_update.model_dump(exclude_unset=True)
    devices_db[device_index].update(update_data)
    
    return devices_db[device_index]


@router.delete("/{device_id}")
async def delete_device(device_id: str):
    """删除设备"""
    device_index = next((i for i, d in enumerate(devices_db) if d["device_id"] == device_id), None)
    if device_index is None:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 删除设备
    devices_db.pop(device_index)
    
    # 删除设备状态
    status_index = next((i for i, s in enumerate(device_statuses) if s["device_id"] == device_id), None)
    if status_index is not None:
        device_statuses.pop(status_index)
    
    # 断开设备连接
    if device_id in device_manager.active_connections:
        device_manager.disconnect(device_id)
    
    return {"message": "设备删除成功"}


@router.get("/{device_id}/status", response_model=DeviceStatus)
async def get_device_status(device_id: str):
    """获取设备状态"""
    status = next((s for s in device_statuses if s["device_id"] == device_id), None)
    if not status:
        raise HTTPException(status_code=404, detail="设备状态不存在")
    return status


@router.post("/{device_id}/data")
async def receive_device_data(device_id: str, data: Dict[str, Any]):
    """接收设备数据（HTTP方式）"""
    # 检查设备是否存在
    device = next((d for d in devices_db if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 处理设备数据
    print(f"收到设备 {device_id} 的数据: {data}")
    
    # 更新设备状态
    status = next((s for s in device_statuses if s["device_id"] == device_id), None)
    if status:
        status["status"] = "online"
        status["last_seen"] = "2026-02-04T10:00:00Z"  # 实际应使用当前时间
    
    # 这里可以添加数据存储、分析等逻辑
    
    return {"message": "数据接收成功", "device_id": device_id}


@router.post("/{device_id}/command")
async def send_device_command(device_id: str, command: Dict[str, Any]):
    """发送命令到设备"""
    # 检查设备是否存在
    device = next((d for d in devices_db if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 检查设备是否在线
    status = next((s for s in device_statuses if s["device_id"] == device_id), None)
    if not status or status["status"] != "online":
        raise HTTPException(status_code=400, detail="设备离线，无法发送命令")
    
    # 根据协议发送命令
    if device["protocol"] == "WebSocket":
        # 通过WebSocket发送命令
        await device_manager.send_personal_message(
            {"type": "command", "command": command},
            device_id
        )
    elif device["protocol"] == "HTTP":
        # 通过HTTP回调发送命令（模拟）
        print(f"通过HTTP发送命令到设备 {device_id}: {command}")
    elif device["protocol"] == "MQTT":
        # 通过MQTT发送命令（模拟）
        print(f"通过MQTT发送命令到设备 {device_id}: {command}")
    else:
        raise HTTPException(status_code=400, detail=f"不支持的协议: {device['protocol']}")
    
    return {"message": "命令发送成功", "device_id": device_id, "command": command}


@router.get("/status/all", response_model=List[DeviceStatus])
async def get_all_device_statuses():
    """获取所有设备状态"""
    return device_statuses


@router.websocket("/ws/{device_id}")
async def websocket_device_endpoint(websocket: WebSocket, device_id: str):
    """设备WebSocket连接端点"""
    # 检查设备是否存在
    device = next((d for d in devices_db if d["device_id"] == device_id), None)
    if not device:
        await websocket.close(code=1008, reason="设备不存在")
        return
    
    # 检查设备协议是否支持WebSocket
    if device["protocol"] != "WebSocket":
        await websocket.close(code=1008, reason="设备协议不支持WebSocket")
        return
    
    # 接受连接
    await device_manager.connect(websocket, device_id)
    
    # 更新设备状态
    status = next((s for s in device_statuses if s["device_id"] == device_id), None)
    if status:
        status["status"] = "online"
        status["last_seen"] = "2026-02-04T10:00:00Z"  # 实际应使用当前时间
    
    try:
        while True:
            # 接收设备消息
            data = await websocket.receive_json()
            
            # 处理设备消息
            print(f"收到设备 {device_id} 的WebSocket消息: {data}")
            
            # 根据消息类型处理
            message_type = data.get("type", "data")
            
            if message_type == "data":
                # 处理设备数据
                print(f"处理设备 {device_id} 的数据: {data.get('data', {})}")
                
                # 发送确认消息
                await device_manager.send_personal_message(
                    {"type": "ack", "message": "数据接收成功", "timestamp": "2026-02-04T10:00:00Z"},
                    device_id
                )
            
            elif message_type == "heartbeat":
                # 处理心跳消息
                print(f"收到设备 {device_id} 的心跳")
                
                # 更新设备状态
                if status:
                    status["last_seen"] = "2026-02-04T10:00:00Z"  # 实际应使用当前时间
                    status["signal_strength"] = data.get("signal_strength", 0.0)
                
                # 发送心跳响应
                await device_manager.send_personal_message(
                    {"type": "heartbeat_ack", "timestamp": "2026-02-04T10:00:00Z"},
                    device_id
                )
    
    except WebSocketDisconnect:
        device_manager.disconnect(device_id)
        
        # 更新设备状态
        if status:
            status["status"] = "offline"
        
        print(f"设备 {device_id} 断开WebSocket连接")
    
    except Exception as e:
        print(f"设备 {device_id} WebSocket错误: {str(e)}")
        device_manager.disconnect(device_id)
        
        # 更新设备状态
        if status:
            status["status"] = "offline"


@router.get("/stats/summary")
async def get_device_stats():
    """获取设备统计信息"""
    total_devices = len(devices_db)
    online_devices = len([s for s in device_statuses if s["status"] == "online"])
    offline_devices = total_devices - online_devices
    
    # 按设备类型统计
    device_types = {}
    for device in devices_db:
        device_type = device["device_type"]
        device_types[device_type] = device_types.get(device_type, 0) + 1
    
    # 按协议统计
    protocols = {}
    for device in devices_db:
        protocol = device["protocol"]
        protocols[protocol] = protocols.get(protocol, 0) + 1
    
    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "device_types": device_types,
        "protocols": protocols,
        "connected_devices": len(device_manager.active_connections)
    }
