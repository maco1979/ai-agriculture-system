"""
远程命令执行服务 - A2A (Agent-to-Agent) 安全传输
实现跨机器远程命令执行，支持权限验证、命令白名单、安全传输
"""

import asyncio
import hashlib
import hmac
import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """命令执行状态"""
    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 执行中
    SUCCESS = "success"           # 执行成功
    FAILED = "failed"             # 执行失败
    TIMEOUT = "timeout"           # 执行超时
    REJECTED = "rejected"         # 被拒绝（权限不足或命令不在白名单）
    CANCELLED = "cancelled"       # 已取消


class PermissionLevel(Enum):
    """权限级别"""
    READONLY = "readonly"         # 只读（查看状态、日志）
    OPERATOR = "operator"         # 操作员（重启服务、清理缓存）
    ADMIN = "admin"               # 管理员（系统配置、用户管理）
    ROOT = "root"                 # 超级用户（所有命令）


@dataclass
class RemoteCommand:
    """远程命令"""
    command_id: str = field(default_factory=lambda: str(uuid4()))
    target_node: str = ""                        # 目标节点ID
    command: str = ""                            # 命令内容
    args: List[str] = field(default_factory=list)  # 命令参数
    working_dir: Optional[str] = None            # 工作目录
    env_vars: Dict[str, str] = field(default_factory=dict)  # 环境变量
    timeout: int = 60                            # 超时时间（秒）
    require_sudo: bool = False                   # 是否需要sudo
    permission_level: PermissionLevel = PermissionLevel.OPERATOR
    timestamp: float = field(default_factory=time.time)
    signature: Optional[str] = None              # 数字签名


@dataclass
class CommandResult:
    """命令执行结果"""
    command_id: str = ""
    status: CommandStatus = CommandStatus.PENDING
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    node_id: str = ""
    error_message: Optional[str] = None


class CommandWhitelist:
    """命令白名单管理"""
    
    # 默认命令白名单（按权限级别分类）
    DEFAULT_WHITELIST: Dict[PermissionLevel, Set[str]] = {
        PermissionLevel.READONLY: {
            "whoami", "pwd", "ls", "cat", "echo", "ps", "top", "df", "free",
            "uptime", "date", "uname", "hostname", "ifconfig", "ip", "netstat",
            "systemctl status", "service status", "docker ps", "docker images",
            "nvidia-smi", " sensors", "nvidia-smi",
        },
        PermissionLevel.OPERATOR: {
            "systemctl restart", "systemctl start", "systemctl stop",
            "service restart", "service start", "service stop",
            "docker restart", "docker start", "docker stop", "docker logs",
            "docker pull", "docker-compose up", "docker-compose down",
            "rm -rf /tmp/", "rm -rf /var/log/", "find", "grep", "awk",
            "python", "python3", "pip", "pip3", "npm", "node",
            "git pull", "git status", "git log",
        },
        PermissionLevel.ADMIN: {
            "systemctl enable", "systemctl disable",
            "apt-get", "apt", "yum", "dnf", "pacman",
            "useradd", "usermod", "userdel",
            "chmod", "chown", "chgrp",
            "mount", "umount", "fdisk", "mkfs",
            "iptables", "ufw", "firewall-cmd",
            "nginx -s", "apachectl",
        },
        PermissionLevel.ROOT: {
            "*",  # 允许所有命令
        }
    }
    
    def __init__(self, custom_whitelist: Optional[Dict[PermissionLevel, Set[str]]] = None):
        self.whitelist = custom_whitelist or self.DEFAULT_WHITELIST
        self._compiled_patterns: Dict[PermissionLevel, List[str]] = {}
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译白名单模式"""
        for level, commands in self.whitelist.items():
            self._compiled_patterns[level] = list(commands)
    
    def is_allowed(self, command: str, level: PermissionLevel) -> bool:
        """检查命令是否允许执行"""
        # ROOT权限允许所有
        if level == PermissionLevel.ROOT:
            return True
        
        # 获取该级别及以下的所有允许命令
        allowed_commands: Set[str] = set()
        for perm_level in PermissionLevel:
            if perm_level.value <= level.value:
                allowed_commands.update(self.whitelist.get(perm_level, set()))
        
        # 检查命令是否匹配白名单
        cmd_base = command.split()[0] if command else ""
        
        for allowed in allowed_commands:
            if allowed == "*":
                return True
            if command.startswith(allowed) or cmd_base == allowed:
                return True
        
        return False
    
    def add_command(self, command: str, level: PermissionLevel):
        """添加命令到白名单"""
        if level not in self.whitelist:
            self.whitelist[level] = set()
        self.whitelist[level].add(command)
        self._compile_patterns()
    
    def remove_command(self, command: str, level: PermissionLevel):
        """从白名单移除命令"""
        if level in self.whitelist and command in self.whitelist[level]:
            self.whitelist[level].remove(command)
            self._compile_patterns()


class SecureTransport:
    """A2A安全传输层"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
    
    def sign_command(self, command: RemoteCommand) -> str:
        """为命令生成数字签名"""
        # 创建命令数据的规范化字符串
        data = f"{command.command_id}:{command.target_node}:{command.command}:{command.timestamp}"
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            self.secret_key,
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_command(self, command: RemoteCommand) -> bool:
        """验证命令签名"""
        if not command.signature:
            return False
        
        expected_signature = self.sign_command(command)
        return hmac.compare_digest(command.signature, expected_signature)
    
    def encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """加密传输数据（简化版，实际应使用AES/RSA）"""
        # 这里使用简单的混淆，生产环境应使用真正的加密
        json_str = json.dumps(payload)
        # 添加时间戳防止重放攻击
        timestamp = str(int(time.time()))
        data = f"{timestamp}:{json_str}"
        
        # 使用HMAC生成校验码
        checksum = hmac.new(self.secret_key, data.encode('utf-8'), hashlib.sha256).hexdigest()[:16]
        return f"{timestamp}:{checksum}:{json_str}"
    
    def decrypt_payload(self, encrypted: str) -> Optional[Dict[str, Any]]:
        """解密传输数据"""
        try:
            parts = encrypted.split(":", 2)
            if len(parts) != 3:
                return None
            
            timestamp, checksum, json_str = parts
            
            # 验证时间戳（防止重放攻击，5分钟有效期）
            msg_time = int(timestamp)
            if abs(time.time() - msg_time) > 300:
                logger.warning("消息时间戳过期，可能是重放攻击")
                return None
            
            # 验证校验码
            data = f"{timestamp}:{json_str}"
            expected_checksum = hmac.new(self.secret_key, data.encode('utf-8'), hashlib.sha256).hexdigest()[:16]
            if not hmac.compare_digest(checksum, expected_checksum):
                logger.warning("校验码不匹配，数据可能被篡改")
                return None
            
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return None


class RemoteCommandExecutor:
    """远程命令执行器 - 在边缘节点上运行"""
    
    def __init__(
        self,
        node_id: str,
        secret_key: str,
        whitelist: Optional[CommandWhitelist] = None
    ):
        self.node_id = node_id
        self.secure_transport = SecureTransport(secret_key)
        self.whitelist = whitelist or CommandWhitelist()
        self.command_history: List[CommandResult] = []
        self.max_history = 1000
        self.running_commands: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            "on_command_received": [],
            "on_command_completed": [],
            "on_command_failed": [],
        }
    
    def register_callback(self, event: str, callback: Callable):
        """注册事件回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, *args, **kwargs):
        """触发事件回调"""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")
    
    async def receive_command(self, encrypted_command: str) -> CommandResult:
        """接收并执行远程命令"""
        result = CommandResult(command_id="", node_id=self.node_id)
        
        try:
            # 解密命令
            payload = self.secure_transport.decrypt_payload(encrypted_command)
            if not payload:
                result.status = CommandStatus.REJECTED
                result.error_message = "命令解密失败或签名无效"
                return result
            
            # 解析命令
            command = RemoteCommand(**payload)
            result.command_id = command.command_id
            
            # 验证签名
            if not self.secure_transport.verify_command(command):
                result.status = CommandStatus.REJECTED
                result.error_message = "命令签名验证失败"
                return result
            
            # 检查命令白名单
            if not self.whitelist.is_allowed(command.command, command.permission_level):
                result.status = CommandStatus.REJECTED
                result.error_message = f"命令 '{command.command}' 不在白名单中或权限不足"
                logger.warning(f"命令被拒绝: {command.command}, 权限: {command.permission_level}")
                return result
            
            # 触发接收回调
            self._trigger_callback("on_command_received", command)
            
            # 执行命令
            result = await self._execute_command(command)
            
            # 触发完成回调
            if result.status == CommandStatus.SUCCESS:
                self._trigger_callback("on_command_completed", command, result)
            else:
                self._trigger_callback("on_command_failed", command, result)
            
            # 保存历史
            self._add_to_history(result)
            
            return result
            
        except Exception as e:
            logger.error(f"处理远程命令失败: {e}")
            result.status = CommandStatus.FAILED
            result.error_message = str(e)
            return result
    
    async def _execute_command(self, command: RemoteCommand) -> CommandResult:
        """执行本地命令"""
        result = CommandResult(
            command_id=command.command_id,
            node_id=self.node_id,
            start_time=datetime.now(),
            status=CommandStatus.RUNNING
        )
        
        try:
            # 构建完整命令
            full_command = [command.command] + command.args
            
            # 如果需要sudo，添加到命令前
            if command.require_sudo:
                full_command = ["sudo", "-n"] + full_command
            
            logger.info(f"执行命令: {' '.join(full_command)}")
            
            # 创建进程
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=command.working_dir,
                env={**dict(subprocess.os.environ), **command.env_vars} if command.env_vars else None
            )
            
            # 记录运行中的命令
            self.running_commands[command.command_id] = process
            
            # 等待完成或超时
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=command.timeout
                )
                
                result.stdout = stdout.decode('utf-8', errors='ignore')
                result.stderr = stderr.decode('utf-8', errors='ignore')
                result.exit_code = process.returncode
                result.status = CommandStatus.SUCCESS if process.returncode == 0 else CommandStatus.FAILED
                
            except asyncio.TimeoutError:
                process.kill()
                result.status = CommandStatus.TIMEOUT
                result.error_message = f"命令执行超时（{command.timeout}秒）"
            
            finally:
                # 从运行中移除
                self.running_commands.pop(command.command_id, None)
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            result.status = CommandStatus.FAILED
            result.error_message = str(e)
        
        finally:
            result.end_time = datetime.now()
            if result.start_time:
                result.execution_time = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    async def cancel_command(self, command_id: str) -> bool:
        """取消正在执行的命令"""
        if command_id in self.running_commands:
            process = self.running_commands[command_id]
            try:
                process.kill()
                return True
            except Exception as e:
                logger.error(f"取消命令失败: {e}")
        return False
    
    def _add_to_history(self, result: CommandResult):
        """添加到历史记录"""
        self.command_history.append(result)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
    
    def get_command_history(
        self,
        limit: int = 100,
        status: Optional[CommandStatus] = None
    ) -> List[CommandResult]:
        """获取命令历史"""
        history = self.command_history
        if status:
            history = [h for h in history if h.status == status]
        return history[-limit:]
    
    def get_command_result(self, command_id: str) -> Optional[CommandResult]:
        """获取特定命令的结果"""
        for result in reversed(self.command_history):
            if result.command_id == command_id:
                return result
        return None
    
    def get_running_commands(self) -> List[str]:
        """获取正在执行的命令ID列表"""
        return list(self.running_commands.keys())


class RemoteCommandClient:
    """远程命令客户端 - 在主控中心使用"""
    
    def __init__(self, secret_key: str, gateway_url: Optional[str] = None):
        self.secure_transport = SecureTransport(secret_key)
        self.gateway_url = gateway_url
        self.pending_commands: Dict[str, RemoteCommand] = {}
    
    def create_command(
        self,
        target_node: str,
        command: str,
        args: Optional[List[str]] = None,
        timeout: int = 60,
        require_sudo: bool = False,
        permission_level: PermissionLevel = PermissionLevel.OPERATOR,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> RemoteCommand:
        """创建远程命令"""
        cmd = RemoteCommand(
            target_node=target_node,
            command=command,
            args=args or [],
            timeout=timeout,
            require_sudo=require_sudo,
            permission_level=permission_level,
            working_dir=working_dir,
            env_vars=env_vars or {}
        )
        
        # 生成签名
        cmd.signature = self.secure_transport.sign_command(cmd)
        
        # 保存到待发送列表
        self.pending_commands[cmd.command_id] = cmd
        
        return cmd
    
    def encrypt_command(self, command: RemoteCommand) -> str:
        """加密命令用于传输"""
        payload = {
            "command_id": command.command_id,
            "target_node": command.target_node,
            "command": command.command,
            "args": command.args,
            "working_dir": command.working_dir,
            "env_vars": command.env_vars,
            "timeout": command.timeout,
            "require_sudo": command.require_sudo,
            "permission_level": command.permission_level.value,
            "timestamp": command.timestamp,
            "signature": command.signature
        }
        return self.secure_transport.encrypt_payload(payload)
    
    async def send_command(
        self,
        target_node: str,
        command: str,
        args: Optional[List[str]] = None,
        timeout: int = 60,
        require_sudo: bool = False,
        permission_level: PermissionLevel = PermissionLevel.OPERATOR,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """发送远程命令（简化版，实际需要HTTP/WebSocket客户端）"""
        cmd = self.create_command(
            target_node=target_node,
            command=command,
            args=args,
            timeout=timeout,
            require_sudo=require_sudo,
            permission_level=permission_level,
            working_dir=working_dir,
            env_vars=env_vars
        )
        
        encrypted = self.encrypt_command(cmd)
        
        # 这里应该通过网络发送到目标节点
        # 简化版返回加密后的命令
        return {
            "command_id": cmd.command_id,
            "encrypted": encrypted,
            "target_node": target_node,
            "status": "sent"
        }
    
    def get_pending_commands(self) -> List[RemoteCommand]:
        """获取待发送的命令"""
        return list(self.pending_commands.values())
    
    def remove_pending_command(self, command_id: str):
        """移除待发送命令"""
        self.pending_commands.pop(command_id, None)


# 全局实例管理
_executors: Dict[str, RemoteCommandExecutor] = {}
_clients: Dict[str, RemoteCommandClient] = {}


def get_executor(node_id: str, secret_key: str) -> RemoteCommandExecutor:
    """获取或创建执行器实例"""
    if node_id not in _executors:
        _executors[node_id] = RemoteCommandExecutor(node_id, secret_key)
    return _executors[node_id]


def get_client(secret_key: str, gateway_url: Optional[str] = None) -> RemoteCommandClient:
    """获取或创建客户端实例"""
    client_id = f"{gateway_url or 'local'}_{hashlib.md5(secret_key.encode()).hexdigest()[:8]}"
    if client_id not in _clients:
        _clients[client_id] = RemoteCommandClient(secret_key, gateway_url)
    return _clients[client_id]
