"""监控数据存储服务
提供监控数据的持久化存储功能
"""

import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.core.config.monitoring_config import monitoring_config

logger = logging.getLogger(__name__)


class MonitoringStorageService:
    """监控数据存储服务"""
    
    def __init__(self):
        """初始化存储服务"""
        self.storage_dir = Path("./monitoring_data")
        self.storage_dir.mkdir(exist_ok=True)
        self._lock = asyncio.Lock()
        self._last_cleanup = datetime.now()
    
    async def store_metrics(self, metrics: Dict[str, Any]):
        """存储监控指标
        
        Args:
            metrics: 监控指标数据
        """
        if not monitoring_config.STORAGE_ENABLED:
            return
        
        async with self._lock:
            try:
                # 创建日期目录
                today = datetime.now().strftime("%Y-%m-%d")
                day_dir = self.storage_dir / today
                day_dir.mkdir(exist_ok=True)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%H-%M-%S")
                file_path = day_dir / f"metrics_{timestamp}.json"
                
                # 写入数据
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(metrics, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"监控指标已存储: {file_path}")
                
                # 定期清理过期数据
                await self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"存储监控指标失败: {e}")
    
    async def store_alert(self, alert: Dict[str, Any]):
        """存储告警数据
        
        Args:
            alert: 告警数据
        """
        if not monitoring_config.STORAGE_ENABLED:
            return
        
        async with self._lock:
            try:
                # 创建告警目录
                alerts_dir = self.storage_dir / "alerts"
                alerts_dir.mkdir(exist_ok=True)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                file_path = alerts_dir / f"alert_{timestamp}.json"
                
                # 写入数据
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(alert, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"告警数据已存储: {file_path}")
                
            except Exception as e:
                logger.error(f"存储告警数据失败: {e}")
    
    async def get_metrics_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取历史监控指标
        
        Args:
            days: 天数
        
        Returns:
            历史监控指标列表
        """
        metrics = []
        
        async with self._lock:
            try:
                # 计算起始日期
                start_date = datetime.now() - timedelta(days=days)
                
                # 遍历日期目录
                for day_dir in self.storage_dir.iterdir():
                    if not day_dir.is_dir() or day_dir.name == "alerts":
                        continue
                    
                    # 检查日期是否在范围内
                    try:
                        dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d")
                        if dir_date < start_date:
                            continue
                    except ValueError:
                        continue
                    
                    # 读取当天的所有指标文件
                    for file_path in day_dir.glob("metrics_*.json"):
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                metrics.append(data)
                        except Exception as e:
                            logger.error(f"读取指标文件失败: {file_path}, {e}")
                
            except Exception as e:
                logger.error(f"获取历史监控指标失败: {e}")
        
        # 按时间排序
        metrics.sort(key=lambda x: x.get("timestamp", ""))
        return metrics
    
    async def get_alert_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取历史告警
        
        Args:
            days: 天数
        
        Returns:
            历史告警列表
        """
        alerts = []
        
        async with self._lock:
            try:
                alerts_dir = self.storage_dir / "alerts"
                if not alerts_dir.exists():
                    return alerts
                
                # 计算起始日期
                start_date = datetime.now() - timedelta(days=days)
                
                # 读取所有告警文件
                for file_path in alerts_dir.glob("alert_*.json"):
                    try:
                        # 从文件名提取日期
                        file_name = file_path.name
                        date_str = file_name.replace("alert_", "").replace(".json", "")
                        alert_date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
                        
                        if alert_date < start_date:
                            continue
                        
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            alerts.append(data)
                    except Exception as e:
                        logger.error(f"读取告警文件失败: {file_path}, {e}")
                
            except Exception as e:
                logger.error(f"获取历史告警失败: {e}")
        
        # 按时间排序
        alerts.sort(key=lambda x: x.get("timestamp", ""))
        return alerts
    
    async def _cleanup_old_data(self):
        """清理过期数据"""
        # 每小时清理一次
        if (datetime.now() - self._last_cleanup).total_seconds() < 3600:
            return
        
        self._last_cleanup = datetime.now()
        
        try:
            # 计算过期日期
            cutoff_date = datetime.now() - timedelta(days=monitoring_config.STORAGE_RETENTION_DAYS)
            
            # 清理日期目录
            for day_dir in self.storage_dir.iterdir():
                if not day_dir.is_dir() or day_dir.name == "alerts":
                    continue
                
                try:
                    dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        # 删除目录及其内容
                        for file_path in day_dir.glob("*"):
                            file_path.unlink()
                        day_dir.rmdir()
                        logger.info(f"已清理过期数据目录: {day_dir}")
                except ValueError:
                    continue
            
            # 清理告警目录
            alerts_dir = self.storage_dir / "alerts"
            if alerts_dir.exists():
                for file_path in alerts_dir.glob("alert_*.json"):
                    try:
                        file_name = file_path.name
                        date_str = file_name.replace("alert_", "").replace(".json", "")
                        alert_date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
                        
                        if alert_date < cutoff_date:
                            file_path.unlink()
                            logger.info(f"已清理过期告警文件: {file_path}")
                    except Exception as e:
                        logger.error(f"清理告警文件失败: {file_path}, {e}")
            
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息
        
        Returns:
            存储信息
        """
        try:
            total_size = 0
            file_count = 0
            
            # 计算总大小和文件数
            for root, dirs, files in os.walk(self.storage_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            return {
                "storage_dir": str(self.storage_dir),
                "total_size_bytes": total_size,
                "total_files": file_count,
                "retention_days": monitoring_config.STORAGE_RETENTION_DAYS,
                "enabled": monitoring_config.STORAGE_ENABLED
            }
        except Exception as e:
            logger.error(f"获取存储信息失败: {e}")
            return {
                "error": str(e),
                "enabled": monitoring_config.STORAGE_ENABLED
            }


# 全局存储服务实例
_monitoring_storage_service: Optional[MonitoringStorageService] = None


def get_monitoring_storage_service() -> MonitoringStorageService:
    """获取监控存储服务单例"""
    global _monitoring_storage_service
    if _monitoring_storage_service is None:
        _monitoring_storage_service = MonitoringStorageService()
    return _monitoring_storage_service


__all__ = [
    "MonitoringStorageService",
    "get_monitoring_storage_service"
]
