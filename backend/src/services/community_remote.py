"""
社区远程执行服务
集成 A2A 远程命令执行到社区系统
支持 AI 角色代理执行远程命令
"""

import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

import aiohttp
import sys
from pathlib import Path

# 处理导入路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.services.remote_command import RemoteCommandClient, PermissionLevel, get_client

logger = logging.getLogger(__name__)

# 远程执行配置
SECRET_KEY = "your-secret-key-change-in-production"

# 命令解析正则
COMMAND_PATTERNS = {
    "nodes": r"^/nodes\s*$",
    "status": r"^/status\s+(\S+)",
    "exec": r"^/exec\s+(\S+)\s+(.+)",
    "batch": r"^/batch\s+(.+)",
    "presets": r"^/presets\s*$",
    "preset_exec": r"^/preset\s+(\S+)\s+(\S+)",
}

# 节点注册表（从 remote_execution 模块共享）
NODE_REGISTRY: Dict[str, Dict[str, Any]] = {}


def set_node_registry(registry: Dict[str, Dict[str, Any]]):
    """设置节点注册表（由 remote_execution 模块调用）"""
    global NODE_REGISTRY
    NODE_REGISTRY = registry


def parse_remote_command(text: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    解析社区消息中的远程执行命令
    
    返回: (command_type, params)
    """
    text = text.strip()
    
    # 检查各个命令模式
    for cmd_type, pattern in COMMAND_PATTERNS.items():
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            params = {"raw": text}
            
            if cmd_type == "nodes":
                return cmd_type, params
            elif cmd_type == "status":
                params["node_id"] = match.group(1)
                return cmd_type, params
            elif cmd_type == "exec":
                params["node_id"] = match.group(1)
                params["command"] = match.group(2)
                return cmd_type, params
            elif cmd_type == "batch":
                params["command"] = match.group(1)
                return cmd_type, params
            elif cmd_type == "presets":
                return cmd_type, params
            elif cmd_type == "preset_exec":
                params["preset_name"] = match.group(1)
                params["node_id"] = match.group(2)
                return cmd_type, params
    
    return None, {}


async def execute_remote_command_by_ai(
    command_type: str,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    执行远程命令（供 AI 角色调用）
    
    返回格式化的执行结果
    """
    
    if command_type == "nodes":
        return await _cmd_list_nodes()
    elif command_type == "status":
        return await _cmd_node_status(params.get("node_id", ""))
    elif command_type == "exec":
        return await _cmd_exec_command(params.get("node_id", ""), params.get("command", ""))
    elif command_type == "batch":
        return await _cmd_batch_exec(params.get("command", ""))
    elif command_type == "presets":
        return await _cmd_list_presets()
    elif command_type == "preset_exec":
        return await _cmd_preset_exec(params.get("preset_name", ""), params.get("node_id", ""))
    
    return {
        "success": False,
        "message": "未知的命令类型",
        "output": ""
    }


async def _cmd_list_nodes() -> Dict[str, Any]:
    """列出所有节点"""
    if not NODE_REGISTRY:
        return {
            "success": True,
            "message": "📭 当前没有已注册的边缘节点",
            "output": "使用边缘计算客户端注册节点后，这里会显示可用节点列表。"
        }
    
    lines = ["📡 已注册的边缘节点：\n"]
    for node_id, info in NODE_REGISTRY.items():
        status = info.get("status", "unknown")
        status_emoji = "🟢" if status == "online" else "🔴" if status == "offline" else "⚪"
        address = info.get("address", "未配置")
        last_heartbeat = info.get("last_heartbeat", "从未")
        
        lines.append(f"{status_emoji} **{node_id}**")
        lines.append(f"   地址: {address}")
        lines.append(f"   状态: {status}")
        lines.append(f"   最后心跳: {last_heartbeat}")
        lines.append("")
    
    return {
        "success": True,
        "message": f"找到 {len(NODE_REGISTRY)} 个节点",
        "output": "\n".join(lines)
    }


async def _cmd_node_status(node_id: str) -> Dict[str, Any]:
    """查看节点状态"""
    if node_id not in NODE_REGISTRY:
        return {
            "success": False,
            "message": f"❌ 节点 '{node_id}' 未找到",
            "output": "请先使用 /nodes 查看可用节点列表。"
        }
    
    node_info = NODE_REGISTRY[node_id]
    
    # 尝试获取实时状态
    try:
        import aiohttp
        node_address = node_info.get("address")
        if node_address:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{node_address}/status", timeout=10) as resp:
                    if resp.status == 200:
                        real_time_status = await resp.json()
                        return {
                            "success": True,
                            "message": f"🖥️ 节点 {node_id} 实时状态",
                            "output": _format_node_status(real_time_status)
                        }
    except Exception as e:
        logger.warning(f"获取节点 {node_id} 实时状态失败: {e}")
    
    # 返回缓存信息
    lines = [
        f"📊 节点 **{node_id}** 信息",
        f"",
        f"状态: {node_info.get('status', 'unknown')}",
        f"地址: {node_info.get('address', '未配置')}",
        f"注册时间: {node_info.get('registered_at', '未知')}",
        f"最后心跳: {node_info.get('last_heartbeat', '从未')}",
    ]
    
    system_info = node_info.get("system_info", {})
    if system_info:
        lines.append(f"")
        lines.append(f"系统信息:")
        lines.append(f"  平台: {system_info.get('platform', '未知')}")
        lines.append(f"  CPU: {system_info.get('cpu_count', '未知')} 核")
        lines.append(f"  内存: {system_info.get('memory_gb', '未知')} GB")
    
    return {
        "success": True,
        "message": f"节点 {node_id} 状态（缓存）",
        "output": "\n".join(lines)
    }


def _format_node_status(status: Dict[str, Any]) -> str:
    """格式化节点状态输出"""
    lines = []
    
    # 系统信息
    sys_info = status.get("system_info", {})
    if sys_info:
        lines.append(f"🖥️ 系统: {sys_info.get('platform', '未知')} {sys_info.get('architecture', '')}")
        lines.append(f"💾 内存: 已用 {sys_info.get('memory_used_gb', '?')} / 总共 {sys_info.get('memory_total_gb', '?')} GB")
        lines.append(f"🔄 CPU: {sys_info.get('cpu_percent', '?')}% 使用率")
    
    # 运行中的命令
    running = status.get("running_commands", [])
    if running:
        lines.append(f"")
        lines.append(f"⏳ 运行中的命令 ({len(running)} 个):")
        for cmd in running[:5]:  # 最多显示5个
            lines.append(f"  • {cmd.get('command', '未知')} (PID: {cmd.get('pid', '?')})")
    
    # 最后更新
    lines.append(f"")
    lines.append(f"🕐 最后更新: {status.get('timestamp', '未知')}")
    
    return "\n".join(lines)


async def _cmd_exec_command(node_id: str, command: str) -> Dict[str, Any]:
    """在指定节点执行命令"""
    if node_id not in NODE_REGISTRY:
        return {
            "success": False,
            "message": f"❌ 节点 '{node_id}' 未找到",
            "output": ""
        }
    
    # 解析命令
    parts = command.split()
    if not parts:
        return {
            "success": False,
            "message": "❌ 命令不能为空",
            "output": ""
        }
    
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    # 创建客户端并发送命令
    try:
        client = get_client(SECRET_KEY)
        node_address = NODE_REGISTRY[node_id].get("address")
        
        result_data = await client.send_command(
            target_node=node_id,
            command=cmd,
            args=args,
            timeout=60,
            require_sudo=False,
            permission_level=PermissionLevel.OPERATOR
        )
        
        # 发送到边缘节点执行
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{node_address}/command",
                json={"encrypted_command": result_data["encrypted"]},
                timeout=300
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return {
                        "success": result.get("success", False),
                        "message": f"✅ 命令执行完成" if result.get("success") else f"❌ 命令执行失败",
                        "output": _format_exec_result(result)
                    }
                else:
                    return {
                        "success": False,
                        "message": f"❌ HTTP {resp.status}",
                        "output": await resp.text()
                    }
                    
    except Exception as e:
        logger.error(f"执行远程命令失败: {e}")
        return {
            "success": False,
            "message": f"❌ 执行失败: {str(e)}",
            "output": ""
        }


def _format_exec_result(result: Dict[str, Any]) -> str:
    """格式化执行结果"""
    lines = []
    
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code")
    
    if stdout:
        lines.append("📤 标准输出:")
        lines.append("```")
        lines.append(stdout[:2000])  # 限制长度
        if len(stdout) > 2000:
            lines.append("... (输出已截断)")
        lines.append("```")
    
    if stderr:
        lines.append("")
        lines.append("⚠️ 错误输出:")
        lines.append("```")
        lines.append(stderr[:1000])
        lines.append("```")
    
    if exit_code is not None:
        lines.append("")
        lines.append(f"🔢 退出码: {exit_code}")
    
    return "\n".join(lines) if lines else "(无输出)"


async def _cmd_batch_exec(command: str) -> Dict[str, Any]:
    """批量执行命令到所有节点"""
    if not NODE_REGISTRY:
        return {
            "success": False,
            "message": "❌ 没有可用的节点",
            "output": ""
        }
    
    results = []
    for node_id in NODE_REGISTRY.keys():
        result = await _cmd_exec_command(node_id, command)
        results.append(f"**{node_id}**: {'✅' if result['success'] else '❌'} {result['message']}")
    
    return {
        "success": True,
        "message": f"📊 批量执行完成 ({len(NODE_REGISTRY)} 个节点)",
        "output": "\n".join(results)
    }


async def _cmd_list_presets() -> Dict[str, Any]:
    """列出预设命令"""
    from src.api.routes.remote_execution import SYSTEM_COMMAND_PRESETS
    
    lines = ["📋 可用预设命令：\n"]
    
    # 按类别分组
    categories = {
        "监控类": [],
        "操作类": [],
        "农业专用": []
    }
    
    for preset in SYSTEM_COMMAND_PRESETS:
        if "监控" in preset.description or preset.name in ["查看系统状态", "查看磁盘空间", "查看内存使用", "查看GPU状态"]:
            categories["监控类"].append(preset)
        elif "农业" in preset.description or "摄像头" in preset.name or "病虫害" in preset.name or "传感器" in preset.name:
            categories["农业专用"].append(preset)
        else:
            categories["操作类"].append(preset)
    
    for category, presets in categories.items():
        if presets:
            lines.append(f"**{category}**")
            for p in presets:
                lines.append(f"  • `{p.name}` - {p.description}")
            lines.append("")
    
    lines.append("使用方法: `/preset <预设名> <节点ID>`")
    
    return {
        "success": True,
        "message": f"共 {len(SYSTEM_COMMAND_PRESETS)} 个预设命令",
        "output": "\n".join(lines)
    }


async def _cmd_preset_exec(preset_name: str, node_id: str) -> Dict[str, Any]:
    """执行预设命令"""
    from src.api.routes.remote_execution import SYSTEM_COMMAND_PRESETS
    
    # 查找预设
    preset = None
    for p in SYSTEM_COMMAND_PRESETS:
        if p.name == preset_name:
            preset = p
            break
    
    if not preset:
        return {
            "success": False,
            "message": f"❌ 预设命令 '{preset_name}' 未找到",
            "output": "使用 /presets 查看可用预设列表。"
        }
    
    # 构建完整命令
    command = f"{preset.command} {' '.join(preset.args)}"
    
    return await _cmd_exec_command(node_id, command)


async def ai_remote_reply(context: str, post_title: str) -> Optional[str]:
    """
    远程执行官 AI 角色的回复逻辑
    
    解析用户输入，如果有远程命令则执行并返回结果
    """
    # 解析命令
    cmd_type, params = parse_remote_command(context)
    
    if cmd_type:
        # 执行远程命令
        result = await execute_remote_command_by_ai(cmd_type, params)
        
        # 构建回复
        reply_lines = [
            f"**{result['message']}**",
            "",
            result['output']
        ]
        
        return "\n".join(reply_lines)
    
    # 没有识别到命令，返回帮助信息
    return (
        "🖥️ **远程执行官** 为您服务！\n\n"
        "我可以帮您管理和操作边缘设备。可用指令：\n\n"
        "• `/nodes` - 查看所有节点\n"
        "• `/status <节点ID>` - 查看节点状态\n"
        "• `/exec <节点ID> <命令>` - 执行远程命令\n"
        "• `/batch <命令>` - 批量执行到所有节点\n"
        "• `/presets` - 查看预设命令\n"
        "• `/preset <预设名> <节点ID>` - 执行预设命令\n\n"
        "💡 示例：`/status edge_001` 或 `/exec edge_001 whoami`"
    )
