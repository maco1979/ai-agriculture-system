# 智能供应链管理服务配置文件
import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # 服务基本配置
    SERVICE_NAME: str = "Smart Supply Chain Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8008"))
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://admin:password@localhost:5432/example_db"
    )
    
    # Redis配置（用于缓存和消息队列）
    REDIS_URL: str = os.getenv(
        "REDIS_URL", 
        "redis://localhost:6379/0"
    )
    
    # API配置
    API_PREFIX: str = "/api/v1/supply-chain"
    CORS_ORIGINS: List[str] = ["*"]
    
    # 供应链管理配置
    SUPPLIER_EVALUATION_THRESHOLD: float = 0.7  # 供应商评估阈值
    INVENTORY_OPTIMIZATION_INTERVAL: int = 3600  # 库存优化间隔（秒）
    DEMAND_FORECAST_HORIZON: int = 30  # 需求预测 horizon（天）
    
    # 物流配置
    LOGISTICS_TRACKING_UPDATE_INTERVAL: int = 600  # 物流跟踪更新间隔（秒）
    ROUTE_OPTIMIZATION_FREQUENCY: int = 1800  # 路线优化频率（秒）
    
    # AI模型配置
    DEMAND_FORECAST_MODEL: str = "prophet"
    SUPPLIER_RISK_MODEL: str = "xgboost"
    
    # 安全配置
    API_KEY: str = os.getenv("API_KEY", "your-secret-api-key")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
