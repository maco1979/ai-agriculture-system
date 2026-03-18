"""监控系统配置
定义监控系统的配置参数
"""

from typing import List, Dict, Any
from pydantic_settings import BaseSettings


class MonitoringConfig(BaseSettings):
    """监控系统配置类"""
    # 系统监控配置
    SYSTEM_MONITOR_UPDATE_INTERVAL: int = 5  # 系统监控更新间隔（秒）
    SYSTEM_MONITOR_HISTORY_SIZE: int = 100  # 系统监控历史数据大小
    
    # 审计监控配置
    AUDIT_MONITOR_ENABLED: bool = True  # 是否启用审计监控
    AUDIT_MONITOR_MAX_ALERTS: int = 1000  # 最大告警历史数量
    
    # 告警配置
    ALERT_ENABLED: bool = True  # 是否启用告警
    ALERT_CHECK_INTERVAL: int = 60  # 告警检查间隔（秒）
    ALERT_SILENCE_DURATION: int = 300  # 告警静默时间（秒）
    
    # 监控指标配置
    METRICS_ENABLED: bool = True  # 是否启用指标收集
    METRICS_EXPORT_INTERVAL: int = 10  # 指标导出间隔（秒）
    
    # 监控存储配置
    STORAGE_ENABLED: bool = True  # 是否启用监控数据存储
    STORAGE_INTERVAL: int = 300  # 存储间隔（秒）
    STORAGE_RETENTION_DAYS: int = 7  # 数据保留天数
    
    # 告警规则配置
    ALERT_RULES: List[Dict[str, Any]] = [
        {
            "name": "HighCPUUsage",
            "description": "CPU使用率过高",
            "condition": "cpu.percent > 80",
            "severity": "warning",
            "for": "5m",
            "enabled": True
        },
        {
            "name": "HighMemoryUsage",
            "description": "内存使用率过高",
            "condition": "memory.percent > 90",
            "severity": "warning",
            "for": "5m",
            "enabled": True
        },
        {
            "name": "DiskSpaceLow",
            "description": "磁盘空间不足",
            "condition": "disk.percent > 95",
            "severity": "critical",
            "for": "10m",
            "enabled": True
        },
        {
            "name": "HighPermissionDenialRate",
            "description": "权限拒绝率过高",
            "condition": "permission_denial_rate > 0.3",
            "severity": "warning",
            "for": "5m",
            "enabled": True
        },
        {
            "name": "CacheHitRateLow",
            "description": "缓存命中率过低",
            "condition": "cache_hit_rate < 0.5",
            "severity": "warning",
            "for": "10m",
            "enabled": True
        },
        {
            "name": "HighRequestLatency",
            "description": "请求延迟过高",
            "condition": "request_latency > 1000",
            "severity": "warning",
            "for": "5m",
            "enabled": True
        },
        {
            "name": "ServiceDown",
            "description": "服务不可用",
            "condition": "service_health == 0",
            "severity": "critical",
            "for": "1m",
            "enabled": True
        }
    ]
    
    # 通知配置
    NOTIFICATION_ENABLED: bool = True  # 是否启用通知
    NOTIFICATION_CHANNELS: List[str] = ["email", "webhook"]  # 通知渠道
    
    # 邮件通知配置
    EMAIL_NOTIFICATION_ENABLED: bool = False  # 是否启用邮件通知
    EMAIL_SENDER: str = "monitoring@example.com"
    EMAIL_RECIPIENTS: List[str] = []
    SMTP_SERVER: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    
    # Webhook通知配置
    WEBHOOK_NOTIFICATION_ENABLED: bool = False  # 是否启用Webhook通知
    WEBHOOK_URL: str = ""
    WEBHOOK_SECRET: str = ""
    
    # 监控仪表板配置
    DASHBOARD_ENABLED: bool = True  # 是否启用仪表板
    DASHBOARD_REFRESH_INTERVAL: int = 5  # 仪表板刷新间隔（秒）
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"  # 从.env文件加载配置
        case_sensitive = True  # 环境变量区分大小写
        extra = "allow"  # 允许额外的字段


# 创建全局监控配置实例
monitoring_config = MonitoringConfig()
