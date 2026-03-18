"""
预测性维护服务配置文件
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """配置类"""
    # 应用配置
    app_name: str = "predictive-maintenance-service"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8005
    
    # 数据库配置
    database_url: str = "sqlite:///./predictive_maintenance.db"
    
    # Redis配置
    redis_url: Optional[str] = None
    
    # 安全配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # 预测性维护配置
    prediction_window: int = 7  # 预测窗口（天）
    anomaly_threshold: float = 0.8  # 异常阈值
    maintenance_threshold: float = 0.6  # 维护阈值
    
    # 模型配置
    model_path: str = "./models"
    model_retrain_interval: int = 7  # 模型重训练间隔（天）
    
    # 监控配置
    monitoring_interval: int = 60  # 监控间隔（秒）
    data_retention_days: int = 90  # 数据保留天数
    
    class Config:
        """配置类配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建配置实例
settings = Settings()
