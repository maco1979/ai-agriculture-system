"""
决策服务配置
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "AI决策服务"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8001
    
    # 数据库配置
    database_url: str = "postgresql://user:password@localhost:5432/ai_platform"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 模型配置
    model_cache_size: int = 100
    model_update_interval: int = 3600
    
    # CORS配置
    cors_origins: List[str] = ["*"]
    
    # 决策服务配置
    decision_timeout: int = 30
    batch_size_limit: int = 100
    metrics_enabled: bool = True
    api_key: str = "your-api-key-here"
    
    # 决策算法参数
    decision_threshold: float = 0.7
    max_decision_time: int = 30
    
    # 监控配置
    prometheus_port: int = 9090

    # ----------------------------------------------------------------
    # 双模型配置（方案A：推理层 + 执行层分离）
    # ----------------------------------------------------------------
    # 推理模型 — 负责复杂分析、病害诊断、深度推理（不支持tools）
    reasoning_model: str = "deepseek-r1:70b"
    reasoning_model_url: str = "http://localhost:11434/v1"
    reasoning_model_timeout: int = 120       # 推理模型响应慢，超时设长
    reasoning_max_tokens: int = 8192

    # 执行模型 — 负责工具调用、OpenClaw Skills、API调度（必须支持tools）
    agent_model: str = "qwen2.5:32b"
    agent_model_url: str = "http://localhost:11434/v1"
    agent_model_timeout: int = 30
    agent_max_tokens: int = 4096

    # 路由策略：auto=自动分流 | reasoning_only | agent_only
    llm_routing_mode: str = "auto"

    # 需要深度推理的关键词（命中则路由到推理模型）
    reasoning_keywords: List[str] = [
        "分析", "诊断", "病害", "原因", "为什么", "评估",
        "报告", "预测", "优化方案", "深度", "推理"
    ]
    # ----------------------------------------------------------------
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

# 全局配置实例（在导入环境可能包含额外 env 时仍能安全构造）
try:
    settings = Settings()
except Exception:
    # 若校验失败，退回到未验证的实例以避免在导入时抛出异常
    settings = Settings.model_construct()