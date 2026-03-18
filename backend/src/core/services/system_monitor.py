"""
系统监控服务
提供异步任务处理和定期系统监控功能
"""

import asyncio
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from collections import deque
import logging

from src.core.config.monitoring_config import monitoring_config
from src.core.services.monitoring_storage_service import get_monitoring_storage_service
from src.core.services.monitoring_notification_service import get_monitoring_notification_service
from src.core.services.audit_monitoring_service import get_audit_monitoring_service

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控器，定期收集系统指标"""
    
    def __init__(self, update_interval: int = 5, history_size: int = 100):
        """初始化系统监控器
        
        Args:
            update_interval: 更新间隔（秒）
            history_size: 历史数据保留数量
        """
        self.update_interval = monitoring_config.SYSTEM_MONITOR_UPDATE_INTERVAL
        self.history_size = monitoring_config.SYSTEM_MONITOR_HISTORY_SIZE
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 历史数据
        self.cpu_history: deque = deque(maxlen=history_size)
        self.memory_history: deque = deque(maxlen=history_size)
        self.network_history: deque = deque(maxlen=history_size)
        
        # 当前状态
        self.current_stats: Dict[str, Any] = {}
        self.last_update: Optional[datetime] = None
        
        # 回调函数
        self._callbacks: list[Callable[[Dict[str, Any]], None]] = []
        
        # 集成服务
        self._storage_service = get_monitoring_storage_service()
        self._notification_service = get_monitoring_notification_service()
        self._audit_service = get_audit_monitoring_service()
        
        # 告警静默记录
        self._alert_silence: Dict[str, datetime] = {}
        
        # 存储计数器
        self._storage_counter = 0
    
    async def start_monitoring(self):
        """启动监控"""
        if self._monitoring:
            logger.warning("监控已在运行中")
            return
        
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"系统监控已启动，更新间隔: {self.update_interval}秒")
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("系统监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._monitoring:
            try:
                # 收集系统指标
                stats = await self._collect_stats()
                
                # 更新当前状态
                self.current_stats = stats
                self.last_update = datetime.now()
                
                # 更新历史数据
                self._update_history(stats)
                
                # 调用回调函数
                for callback in self._callbacks:
                    try:
                        callback(stats)
                    except Exception as e:
                        logger.error(f"监控回调函数执行失败: {e}")
                
                # 定期存储监控数据
                self._storage_counter += 1
                if monitoring_config.STORAGE_ENABLED and self._storage_counter >= (monitoring_config.STORAGE_INTERVAL / self.update_interval):
                    await self._storage_service.store_metrics(stats)
                    self._storage_counter = 0
                
                # 检查系统告警
                await self._check_system_alerts(stats)
                
                # 更新审计监控服务中的系统健康状态
                await self._audit_service.update_system_health("system", True)
                await self._audit_service.update_system_health("cpu", stats.get("cpu", {}).get("percent", 0) < 80)
                await self._audit_service.update_system_health("memory", stats.get("memory", {}).get("percent", 0) < 90)
                await self._audit_service.update_system_health("disk", stats.get("disk", {}).get("percent", 0) < 95)
                
                # 等待下一次更新
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                # 更新系统健康状态为不健康
                await self._audit_service.update_system_health("system", False)
                await asyncio.sleep(self.update_interval)
    
    async def _collect_stats(self) -> Dict[str, Any]:
        """收集系统统计信息"""
        try:
            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=0)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else None
            
            # 内存信息
            memory = psutil.virtual_memory()
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            
            # 网络信息
            net_io = psutil.net_io_counters()
            
            # 进程信息
            process = psutil.Process()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": cpu_freq
                },
                "memory": {
                    "percent": memory.percent,
                    "available": memory.available,
                    "used": memory.used,
                    "total": memory.total
                },
                "disk": {
                    "percent": disk.percent,
                    "used": disk.used,
                    "free": disk.free,
                    "total": disk.total
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent if net_io else 0,
                    "bytes_recv": net_io.bytes_recv if net_io else 0,
                    "packets_sent": net_io.packets_sent if net_io else 0,
                    "packets_recv": net_io.packets_recv if net_io else 0
                },
                "process": {
                    "pid": os.getpid(),
                    "create_time": process.create_time(),
                    "memory_info": process.memory_info()._asdict(),
                    "cpu_percent": process.cpu_percent()
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"收集系统统计信息失败: {e}")
            return {}
    
    def _update_history(self, stats: Dict[str, Any]):
        """更新历史数据"""
        if not stats:
            return
        
        # 更新CPU历史
        self.cpu_history.append({
            "timestamp": stats.get("timestamp"),
            "percent": stats.get("cpu", {}).get("percent", 0)
        })
        
        # 更新内存历史
        self.memory_history.append({
            "timestamp": stats.get("timestamp"),
            "percent": stats.get("memory", {}).get("percent", 0)
        })
        
        # 更新网络历史
        self.network_history.append({
            "timestamp": stats.get("timestamp"),
            "bytes_sent": stats.get("network", {}).get("bytes_sent", 0),
            "bytes_recv": stats.get("network", {}).get("bytes_recv", 0)
        })
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加回调函数
        
        Args:
            callback: 回调函数，接收系统统计信息
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """移除回调函数
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        return self.current_stats
    
    def get_history(self, metric_type: str = "cpu") -> list:
        """获取历史数据
        
        Args:
            metric_type: 指标类型 ("cpu", "memory", "network")
        
        Returns:
            历史数据列表
        """
        if metric_type == "cpu":
            return list(self.cpu_history)
        elif metric_type == "memory":
            return list(self.memory_history)
        elif metric_type == "network":
            return list(self.network_history)
        else:
            return []
    
    async def _check_system_alerts(self, stats: Dict[str, Any]):
        """检查系统告警"""
        current_time = datetime.now()
        
        # 清理过期的静默告警
        self._alert_silence = {
            alert_name: silence_time
            for alert_name, silence_time in self._alert_silence.items()
            if silence_time > current_time
        }
        
        # 检查CPU使用率
        cpu_percent = stats.get("cpu", {}).get("percent", 0)
        if cpu_percent > 80:
            alert_name = "HighCPUUsage"
            if alert_name not in self._alert_silence:
                alert = {
                    "name": alert_name,
                    "description": "CPU使用率过高",
                    "severity": "warning",
                    "value": cpu_percent,
                    "condition": "cpu.percent > 80",
                    "timestamp": current_time.isoformat()
                }
                await self._storage_service.store_alert(alert)
                await self._notification_service.send_alert_notification(alert)
                self._alert_silence[alert_name] = current_time + timedelta(seconds=monitoring_config.ALERT_SILENCE_DURATION)
        
        # 检查内存使用率
        memory_percent = stats.get("memory", {}).get("percent", 0)
        if memory_percent > 90:
            alert_name = "HighMemoryUsage"
            if alert_name not in self._alert_silence:
                alert = {
                    "name": alert_name,
                    "description": "内存使用率过高",
                    "severity": "warning",
                    "value": memory_percent,
                    "condition": "memory.percent > 90",
                    "timestamp": current_time.isoformat()
                }
                await self._storage_service.store_alert(alert)
                await self._notification_service.send_alert_notification(alert)
                self._alert_silence[alert_name] = current_time + timedelta(seconds=monitoring_config.ALERT_SILENCE_DURATION)
        
        # 检查磁盘空间
        disk_percent = stats.get("disk", {}).get("percent", 0)
        if disk_percent > 95:
            alert_name = "DiskSpaceLow"
            if alert_name not in self._alert_silence:
                alert = {
                    "name": alert_name,
                    "description": "磁盘空间不足",
                    "severity": "critical",
                    "value": disk_percent,
                    "condition": "disk.percent > 95",
                    "timestamp": current_time.isoformat()
                }
                await self._storage_service.store_alert(alert)
                await self._notification_service.send_alert_notification(alert)
                self._alert_silence[alert_name] = current_time + timedelta(seconds=monitoring_config.ALERT_SILENCE_DURATION)
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        if not self.cpu_history:
            return {}
        
        # 计算CPU统计
        cpu_values = [item["percent"] for item in self.cpu_history]
        cpu_avg = sum(cpu_values) / len(cpu_values)
        cpu_max = max(cpu_values)
        cpu_min = min(cpu_values)
        
        # 计算内存统计
        memory_values = [item["percent"] for item in self.memory_history]
        memory_avg = sum(memory_values) / len(memory_values)
        memory_max = max(memory_values)
        memory_min = min(memory_values)
        
        return {
            "cpu": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": round(cpu_avg, 2),
                "max": cpu_max,
                "min": cpu_min
            },
            "memory": {
                "current": memory_values[-1] if memory_values else 0,
                "average": round(memory_avg, 2),
                "max": memory_max,
                "min": memory_min
            },
            "history_size": len(self.cpu_history),
            "last_update": self.last_update.isoformat() if self.last_update else None
        }


class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        """初始化异步任务管理器
        
        Args:
            max_concurrent_tasks: 最大并发任务数
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._tasks: Dict[str, asyncio.Task] = {}
        self._task_results: Dict[str, Any] = {}
        self._task_errors: Dict[str, Exception] = {}
    
    async def submit_task(self, task_id: str, coro, timeout: Optional[float] = None) -> Any:
        """提交异步任务
        
        Args:
            task_id: 任务ID
            coro: 协程对象
            timeout: 超时时间（秒）
        
        Returns:
            任务结果
        """
        async with self._semaphore:
            try:
                if timeout:
                    result = await asyncio.wait_for(coro, timeout=timeout)
                else:
                    result = await coro
                
                self._task_results[task_id] = result
                return result
                
            except Exception as e:
                self._task_errors[task_id] = e
                logger.error(f"任务 {task_id} 执行失败: {e}")
                raise
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务结果，如果任务未完成则返回None
        """
        return self._task_results.get(task_id)
    
    def get_task_error(self, task_id: str) -> Optional[Exception]:
        """获取任务错误
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务错误，如果任务没有错误则返回None
        """
        return self._task_errors.get(task_id)
    
    def clear_task(self, task_id: str):
        """清除任务结果
        
        Args:
            task_id: 任务ID
        """
        self._task_results.pop(task_id, None)
        self._task_errors.pop(task_id, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        return {
            "total_tasks": len(self._tasks),
            "completed_tasks": len(self._task_results),
            "failed_tasks": len(self._task_errors),
            "max_concurrent_tasks": self.max_concurrent_tasks
        }


# 全局实例
system_monitor = SystemMonitor(update_interval=5, history_size=100)
async_task_manager = AsyncTaskManager(max_concurrent_tasks=10)


async def start_system_monitor():
    """启动系统监控"""
    await system_monitor.start_monitoring()


async def stop_system_monitor():
    """停止系统监控"""
    await system_monitor.stop_monitoring()


def get_system_monitor() -> SystemMonitor:
    """获取系统监控器实例"""
    return system_monitor


def get_async_task_manager() -> AsyncTaskManager:
    """获取异步任务管理器实例"""
    return async_task_manager


__all__ = [
    "SystemMonitor",
    "AsyncTaskManager",
    "system_monitor",
    "async_task_manager",
    "start_system_monitor",
    "stop_system_monitor",
    "get_system_monitor",
    "get_async_task_manager"
]