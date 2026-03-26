"""
远程命令执行API路由
提供从主控中心向边缘节点发送远程命令的REST API
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from src.services.remote_command import (
    RemoteCommandClient,
    PermissionLevel,
    CommandStatus,
    get_client
)

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/remote", tags=["remote-execution"])

# 全局配置（实际应从配置文件或环境变量读取）
SECRET_KEY = "your-secret-key-change-in-production"
NODE_REGISTRY: Dict[str, Dict[str, Any]] = {}  # 节点注册表


# ============ 请求/响应模型 ============

class RemoteCommandRequest(BaseModel):
    """远程命令请求"""
    target_node: str = Field(..., description="目标节点ID")
    command: str = Field(..., description="命令")
    args: List[str] = Field(default=[], description="命令参数")
    timeout: int = Field(default=60, description="超时时间（秒）", ge=1, le=3600)
    require_sudo: bool = Field(default=False, description="是否需要sudo")
    permission_level: str = Field(default="operator", description="权限级别")
    working_dir: Optional[str] = Field(default=None, description="工作目录")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="环境变量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_node": "edge_001",
                "command": "python",
                "args": ["-c", "print('Hello from edge node')"],
                "timeout": 30,
                "require_sudo": False,
                "permission_level": "operator"
            }
        }


class BatchCommandRequest(BaseModel):
    """批量命令请求"""
    target_nodes: List[str] = Field(..., description="目标节点ID列表")
    command: str = Field(..., description="命令")
    args: List[str] = Field(default=[], description="命令参数")
    timeout: int = Field(default=60, description="超时时间（秒）")
    require_sudo: bool = Field(default=False, description="是否需要sudo")
    permission_level: str = Field(default="operator", description="权限级别")
    parallel: bool = Field(default=True, description="是否并行执行")


class CommandResponse(BaseModel):
    """命令执行响应"""
    success: bool
    command_id: str
    target_node: str
    status: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    timestamp: str


class BatchCommandResponse(BaseModel):
    """批量命令执行响应"""
    total: int
    success_count: int
    failed_count: int
    results: List[CommandResponse]
    execution_time: float


class NodeInfo(BaseModel):
    """节点信息"""
    node_id: str
    node_name: Optional[str] = None
    address: str
    status: str
    last_heartbeat: Optional[str] = None
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class WhitelistEntry(BaseModel):
    """白名单条目"""
    command: str
    permission_level: str


class SystemCommandPreset(BaseModel):
    """系统命令预设"""
    name: str
    description: str
    command: str
    args: List[str] = []
    permission_level: str
    timeout: int = 60


# ============ 预设命令库 ============

SYSTEM_COMMAND_PRESETS: List[SystemCommandPreset] = [
    # 监控类命令
    SystemCommandPreset(
        name="查看系统状态",
        description="显示系统负载、内存和磁盘使用情况",
        command="top",
        args=["-b", "-n", "1"],
        permission_level="readonly",
        timeout=10
    ),
    SystemCommandPreset(
        name="查看磁盘空间",
        description="显示磁盘使用情况",
        command="df",
        args=["-h"],
        permission_level="readonly",
        timeout=10
    ),
    SystemCommandPreset(
        name="查看内存使用",
        description="显示内存使用情况",
        command="free",
        args=["-h"],
        permission_level="readonly",
        timeout=10
    ),
    SystemCommandPreset(
        name="查看GPU状态",
        description="显示NVIDIA GPU状态（如果有）",
        command="nvidia-smi",
        args=[],
        permission_level="readonly",
        timeout=10
    ),
    
    # 操作类命令
    SystemCommandPreset(
        name="重启服务",
        description="重启指定服务",
        command="systemctl",
        args=["restart"],
        permission_level="operator",
        timeout=60
    ),
    SystemCommandPreset(
        name="查看服务日志",
        description="查看服务的最近日志",
        command="journalctl",
        args=["-u", "--lines", "50"],
        permission_level="readonly",
        timeout=15
    ),
    SystemCommandPreset(
        name="清理临时文件",
        description="清理/tmp目录下的临时文件",
        command="rm",
        args=["-rf", "/tmp/*"],
        permission_level="operator",
        timeout=30
    ),
    
    # 农业专用命令
    SystemCommandPreset(
        name="获取摄像头快照",
        description="从边缘摄像头获取当前图像",
        command="python",
        args=["-c", "import cv2; cap = cv2.VideoCapture(0); ret, frame = cap.read(); cv2.imwrite('/tmp/snapshot.jpg', frame) if ret else exit(1)"],
        permission_level="operator",
        timeout=15
    ),
    SystemCommandPreset(
        name="运行病虫害检测",
        description="在边缘设备上运行病虫害检测模型",
        command="python",
        args=["/opt/agriculture/scripts/detect_pests.py"],
        permission_level="operator",
        timeout=120
    ),
    SystemCommandPreset(
        name="校准传感器",
        description="校准温湿度传感器",
        command="python",
        args=["/opt/agriculture/scripts/calibrate_sensors.py"],
        permission_level="operator",
        timeout=60
    ),
    SystemCommandPreset(
        name="查看传感器数据",
        description="获取最新的传感器读数",
        command="cat",
        args=["/opt/agriculture/data/latest_readings.json"],
        permission_level="readonly",
        timeout=10
    ),
]


# ============ API端点 ============

@router.post("/execute", response_model=CommandResponse)
async def execute_remote_command(request: RemoteCommandRequest):
    """
    执行远程命令
    
    向指定的边缘节点发送命令并执行，返回执行结果
    """
    import time
    start_time = time.time()
    
    try:
        # 检查目标节点是否已注册
        if request.target_node not in NODE_REGISTRY:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"节点 '{request.target_node}' 未找到或未注册"
            )
        
        # 解析权限级别
        try:
            permission_level = PermissionLevel(request.permission_level.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的权限级别: {request.permission_level}"
            )
        
        # 创建客户端
        client = get_client(SECRET_KEY)
        
        # 获取节点地址
        node_info = NODE_REGISTRY[request.target_node]
        node_address = node_info.get("address")
        
        # 发送命令
        result_data = await client.send_command(
            target_node=request.target_node,
            command=request.command,
            args=request.args,
            timeout=request.timeout,
            require_sudo=request.require_sudo,
            permission_level=permission_level,
            working_dir=request.working_dir,
            env_vars=request.env_vars
        )
        
        # 这里简化处理，实际应该通过HTTP发送到边缘节点
        # 然后等待响应
        
        # 模拟发送到边缘节点并获取结果
        # 实际实现应该通过HTTP POST到边缘节点的/command端点
        execution_result = await _send_command_to_node(
            node_address,
            result_data["encrypted"]
        )
        
        return CommandResponse(
            success=execution_result.get("success", False),
            command_id=result_data["command_id"],
            target_node=request.target_node,
            status=execution_result.get("status", "unknown"),
            stdout=execution_result.get("stdout"),
            stderr=execution_result.get("stderr"),
            exit_code=execution_result.get("exit_code"),
            execution_time=time.time() - start_time,
            error_message=execution_result.get("error_message"),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行远程命令失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"命令执行失败: {str(e)}"
        )


@router.post("/execute/batch", response_model=BatchCommandResponse)
async def execute_batch_commands(request: BatchCommandRequest):
    """
    批量执行远程命令
    
    向多个边缘节点同时发送命令
    """
    import time
    start_time = time.time()
    
    async def execute_single(node_id: str) -> CommandResponse:
        single_request = RemoteCommandRequest(
            target_node=node_id,
            command=request.command,
            args=request.args,
            timeout=request.timeout,
            require_sudo=request.require_sudo,
            permission_level=request.permission_level
        )
        try:
            return await execute_remote_command(single_request)
        except HTTPException as e:
            return CommandResponse(
                success=False,
                command_id="",
                target_node=node_id,
                status="failed",
                error_message=e.detail,
                timestamp=datetime.now().isoformat()
            )
    
    try:
        if request.parallel:
            # 并行执行
            tasks = [execute_single(node_id) for node_id in request.target_nodes]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 串行执行
            results = []
            for node_id in request.target_nodes:
                result = await execute_single(node_id)
                results.append(result)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(CommandResponse(
                    success=False,
                    command_id="",
                    target_node=request.target_nodes[i],
                    status="failed",
                    error_message=str(result),
                    timestamp=datetime.now().isoformat()
                ))
            else:
                processed_results.append(result)
        
        success_count = sum(1 for r in processed_results if r.success)
        failed_count = len(processed_results) - success_count
        
        return BatchCommandResponse(
            total=len(request.target_nodes),
            success_count=success_count,
            failed_count=failed_count,
            results=processed_results,
            execution_time=time.time() - start_time
        )
        
    except Exception as e:
        logger.error(f"批量执行失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量执行失败: {str(e)}"
        )


@router.get("/nodes", response_model=List[NodeInfo])
async def list_registered_nodes():
    """
    获取所有已注册的节点
    
    返回所有已向主控中心注册的边缘节点列表
    """
    nodes = []
    for node_id, info in NODE_REGISTRY.items():
        nodes.append(NodeInfo(
            node_id=node_id,
            node_name=info.get("node_name"),
            address=info.get("address", ""),
            status=info.get("status", "unknown"),
            last_heartbeat=info.get("last_heartbeat"),
            capabilities=info.get("capabilities", {})
        ))
    return nodes


@router.get("/nodes/{node_id}")
async def get_node_details(node_id: str):
    """
    获取节点详细信息
    """
    if node_id not in NODE_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点 '{node_id}' 未找到"
        )
    
    return NODE_REGISTRY[node_id]


@router.get("/nodes/{node_id}/status")
async def get_node_status(node_id: str):
    """
    获取节点实时状态
    
    向边缘节点查询当前的系统状态和运行信息
    """
    if node_id not in NODE_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点 '{node_id}' 未找到"
        )
    
    try:
        node_address = NODE_REGISTRY[node_id].get("address")
        if not node_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="节点地址未配置"
            )
        
        # 发送HTTP GET请求到节点的/status端点
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{node_address}/status", timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise HTTPException(
                        status_code=resp.status,
                        detail=f"节点返回错误: {resp.status}"
                    )
                    
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="查询节点状态超时"
        )
    except Exception as e:
        logger.error(f"获取节点状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取状态失败: {str(e)}"
        )


@router.post("/nodes/{node_id}/cancel/{command_id}")
async def cancel_remote_command(node_id: str, command_id: str):
    """
    取消正在执行的远程命令
    """
    if node_id not in NODE_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点 '{node_id}' 未找到"
        )
    
    try:
        node_address = NODE_REGISTRY[node_id].get("address")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{node_address}/cancel/{command_id}",
                timeout=10
            ) as resp:
                return await resp.json()
                    
    except Exception as e:
        logger.error(f"取消命令失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消命令失败: {str(e)}"
        )


@router.get("/presets", response_model=List[SystemCommandPreset])
async def list_command_presets():
    """
    获取预设命令列表
    
    返回可用的系统预设命令，包括监控、操作和农业专用命令
    """
    return SYSTEM_COMMAND_PRESETS


@router.post("/presets/{preset_name}/execute")
async def execute_preset_command(preset_name: str, target_node: str):
    """
    执行预设命令
    
    使用预设的命令模板在指定节点上执行
    """
    # 查找预设
    preset = None
    for p in SYSTEM_COMMAND_PRESETS:
        if p.name == preset_name:
            preset = p
            break
    
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"预设命令 '{preset_name}' 未找到"
        )
    
    # 构建请求
    request = RemoteCommandRequest(
        target_node=target_node,
        command=preset.command,
        args=preset.args,
        timeout=preset.timeout,
        permission_level=preset.permission_level
    )
    
    return await execute_remote_command(request)


@router.get("/history/{node_id}")
async def get_node_command_history(node_id: str, limit: int = 100):
    """
    获取节点的命令执行历史
    """
    if node_id not in NODE_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"节点 '{node_id}' 未找到"
        )
    
    try:
        node_address = NODE_REGISTRY[node_id].get("address")
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{node_address}/history?limit={limit}",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise HTTPException(
                        status_code=resp.status,
                        detail="获取历史失败"
                    )
                    
    except Exception as e:
        logger.error(f"获取历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取历史失败: {str(e)}"
        )


# ============ 内部函数 ============

async def _send_command_to_node(node_address: str, encrypted_command: str) -> Dict[str, Any]:
    """发送命令到边缘节点"""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{node_address}/command",
            json={"encrypted_command": encrypted_command},
            timeout=300  # 5分钟超时
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                text = await resp.text()
                return {
                    "success": False,
                    "status": "failed",
                    "error_message": f"HTTP {resp.status}: {text}"
                }


# 供其他模块调用的注册函数
def register_node(node_id: str, node_info: Dict[str, Any]):
    """注册节点"""
    NODE_REGISTRY[node_id] = {
        **node_info,
        "registered_at": datetime.now().isoformat()
    }
    logger.info(f"✅ 节点已注册: {node_id}")


def update_node_heartbeat(node_id: str, heartbeat_data: Dict[str, Any]):
    """更新节点心跳"""
    if node_id in NODE_REGISTRY:
        NODE_REGISTRY[node_id]["last_heartbeat"] = datetime.now().isoformat()
        NODE_REGISTRY[node_id]["system_info"] = heartbeat_data.get("system_info", {})
        NODE_REGISTRY[node_id]["running_commands"] = heartbeat_data.get("running_commands", [])


def unregister_node(node_id: str):
    """注销节点"""
    if node_id in NODE_REGISTRY:
        del NODE_REGISTRY[node_id]
        logger.info(f"🗑️ 节点已注销: {node_id}")
