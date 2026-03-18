"""
监控和日志服务配置
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "监控和日志服务"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8004
    
    # 数据库配置
    database_url: str = "postgresql://user:password@localhost:5432/ai_platform"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 监控配置
    monitoring_enabled: bool = True
    prometheus_port: int = 9090
    metrics_interval: int = 60  # 秒
    alert_threshold: float = 80.0  # 百分比
    
    # 日志配置
    logging_enabled: bool = True
    log_level: str = "INFO"
    log_retention_days: int = 30
    log_rotation_size: int = 10485760  # 10MB
    
    # Elasticsearch配置
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_username: str = "elastic"
    elasticsearch_password: str = "changeme"
    elasticsearch_index: str = "ai-agriculture-logs"
    
    # Kafka配置
    kafka_bootstrap_servers: List[str] = ["localhost:9092"]
    kafka_topic: str = "ai-agriculture-logs"
    kafka_group_id: str = "monitoring-service"
    
    # MongoDB配置
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "ai_platform"
    mongodb_collection: str = "metrics"
    
    # CORS配置
    cors_origins: list[str] = ["*"]
    
    # 安全配置
    api_key: str = "your-api-key-here"
    
    # 服务配置
    services_to_monitor: List[str] = [
        "frontend-web",
        "backend-core",
        "api-gateway",
        "decision-service",
        "edge-computing",
        "blockchain-integration"
    ]
    
    # 健康检查配置
    health_check_interval: int = 30  # 秒
    max_health_check_failures: int = 3
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

# 全局配置实例
settings = Settings()