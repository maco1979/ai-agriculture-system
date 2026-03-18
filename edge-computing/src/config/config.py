"""
边缘计算服务配置
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "边缘计算服务"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8002
    
    # 数据库配置
    database_url: str = "postgresql://user:password@localhost:5432/ai_platform"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 边缘节点配置
    edge_nodes: List[str] = ["localhost:8080", "localhost:8081"]
    node_health_check_interval: int = 60
    max_reconnect_attempts: int = 5
    reconnect_delay: int = 5
    
    # 任务配置
    task_queue_size: int = 1000
    max_concurrent_tasks: int = 10
    task_timeout: int = 300
    
    # 模型配置
    model_cache_size: int = 10
    model_update_interval: int = 3600
    
    # CORS配置
    cors_origins: list[str] = ["*"]
    
    # 边缘计算配置
    edge_computing_enabled: bool = True
    batch_processing_enabled: bool = True
    realtime_processing_enabled: bool = True
    
    # 网络配置
    max_message_size: int = 10485760  # 10MB
    websocket_timeout: int = 3600
    
    # 安全配置
    api_key: str = "your-api-key-here"
    
    # 监控配置
    prometheus_port: int = 9091
    metrics_enabled: bool = True
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

# 全局配置实例
settings = Settings()