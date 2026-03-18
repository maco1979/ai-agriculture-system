"""监控通知服务
提供告警通知功能，支持多种通知渠道
"""

import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.core.config.monitoring_config import monitoring_config

logger = logging.getLogger(__name__)


class MonitoringNotificationService:
    """监控通知服务"""
    
    def __init__(self):
        """初始化通知服务"""
        self._lock = asyncio.Lock()
        self._email_session = None
        self._webhook_session = None
    
    async def send_alert_notification(self, alert: Dict[str, Any]):
        """发送告警通知
        
        Args:
            alert: 告警数据
        """
        if not monitoring_config.NOTIFICATION_ENABLED:
            return
        
        async with self._lock:
            try:
                # 构建通知消息
                message = self._build_notification_message(alert)
                
                # 发送到各个渠道
                tasks = []
                
                if "email" in monitoring_config.NOTIFICATION_CHANNELS:
                    tasks.append(self._send_email_notification(message, alert))
                
                if "webhook" in monitoring_config.NOTIFICATION_CHANNELS:
                    tasks.append(self._send_webhook_notification(message, alert))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
            except Exception as e:
                logger.error(f"发送告警通知失败: {e}")
    
    def _build_notification_message(self, alert: Dict[str, Any]) -> str:
        """构建通知消息
        
        Args:
            alert: 告警数据
        
        Returns:
            通知消息
        """
        severity = alert.get("severity", "info").upper()
        timestamp = alert.get("timestamp", datetime.now().isoformat())
        
        message = f"🚨 监控告警通知 🚨\n"
        message += f"======================================\n"
        message += f"告警名称: {alert.get('name', 'Unknown')}\n"
        message += f"告警级别: {severity}\n"
        message += f"告警描述: {alert.get('description', 'No description')}\n"
        message += f"触发时间: {timestamp}\n"
        
        if "value" in alert:
            message += f"当前值: {alert['value']}\n"
        
        if "condition" in alert:
            message += f"触发条件: {alert['condition']}\n"
        
        message += "======================================"
        
        return message
    
    async def _send_email_notification(self, message: str, alert: Dict[str, Any]):
        """发送邮件通知
        
        Args:
            message: 通知消息
            alert: 告警数据
        """
        if not monitoring_config.EMAIL_NOTIFICATION_ENABLED:
            return
        
        try:
            # 构建邮件
            msg = MIMEMultipart()
            msg["From"] = monitoring_config.EMAIL_SENDER
            msg["To"] = ", ".join(monitoring_config.EMAIL_RECIPIENTS)
            
            severity = alert.get("severity", "info").upper()
            msg["Subject"] = f"[{severity}] 监控告警: {alert.get('name', 'Unknown')}"
            
            msg.attach(MIMEText(message, "plain", "utf-8"))
            
            # 发送邮件
            with smtplib.SMTP(monitoring_config.SMTP_SERVER, monitoring_config.SMTP_PORT) as server:
                server.starttls()
                server.login(monitoring_config.SMTP_USERNAME, monitoring_config.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"邮件通知已发送: {alert.get('name')}")
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
    
    async def _send_webhook_notification(self, message: str, alert: Dict[str, Any]):
        """发送Webhook通知
        
        Args:
            message: 通知消息
            alert: 告警数据
        """
        if not monitoring_config.WEBHOOK_NOTIFICATION_ENABLED:
            return
        
        try:
            # 构建Webhook数据
            webhook_data = {
                "alert": alert,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "severity": alert.get("severity", "info")
            }
            
            # 发送Webhook
            if self._webhook_session is None:
                self._webhook_session = aiohttp.ClientSession()
            
            headers = {
                "Content-Type": "application/json"
            }
            
            if monitoring_config.WEBHOOK_SECRET:
                headers["X-Webhook-Secret"] = monitoring_config.WEBHOOK_SECRET
            
            async with self._webhook_session.post(
                monitoring_config.WEBHOOK_URL,
                json=webhook_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.info(f"Webhook通知已发送: {alert.get('name')}")
                else:
                    logger.error(f"发送Webhook通知失败，状态码: {response.status}")
            
        except Exception as e:
            logger.error(f"发送Webhook通知失败: {e}")
    
    async def send_system_notification(self, title: str, message: str, level: str = "info"):
        """发送系统通知
        
        Args:
            title: 通知标题
            message: 通知消息
            level: 通知级别 (info, warning, error, critical)
        """
        if not monitoring_config.NOTIFICATION_ENABLED:
            return
        
        try:
            notification_data = {
                "name": title,
                "description": message,
                "severity": level,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.send_alert_notification(notification_data)
            
        except Exception as e:
            logger.error(f"发送系统通知失败: {e}")
    
    async def close(self):
        """关闭通知服务"""
        try:
            if self._webhook_session:
                await self._webhook_session.close()
        except Exception as e:
            logger.error(f"关闭通知服务失败: {e}")


# 全局通知服务实例
_monitoring_notification_service: Optional[MonitoringNotificationService] = None


def get_monitoring_notification_service() -> MonitoringNotificationService:
    """获取监控通知服务单例"""
    global _monitoring_notification_service
    if _monitoring_notification_service is None:
        _monitoring_notification_service = MonitoringNotificationService()
    return _monitoring_notification_service


__all__ = [
    "MonitoringNotificationService",
    "get_monitoring_notification_service"
]
