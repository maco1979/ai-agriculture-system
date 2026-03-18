"""
区块链集成服务配置
"""

from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "区块链集成服务"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8003
    
    # 数据库配置
    database_url: str = "postgresql://user:password@localhost:5432/ai_platform"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 区块链配置
    blockchain_enabled: bool = True
    blockchain_network: str = "testnet"  # testnet, mainnet
    blockchain_api_url: str = "https://api.blockchain.com/v3"
    blockchain_api_key: str = "your-api-key-here"
    
    # 智能合约配置
    smart_contract_address: str = "0x1234567890123456789012345678901234567890"
    smart_contract_abi: str = "abi.json"
    gas_price: int = 20  # Gwei
    gas_limit: int = 2000000
    
    # 钱包配置
    wallet_address: str = "0x0987654321098765432109876543210987654321"
    private_key: str = "your-private-key-here"
    
    # 交易配置
    transaction_timeout: int = 300
    transaction_retries: int = 3
    transaction_retry_delay: int = 5
    
    # 奖励池配置
    reward_pool_address: str = "0xabcdef1234567890abcdef1234567890abcdef12"
    reward_pool_enabled: bool = True
    reward_amount: float = 1.0  # 代币数量
    
    # CORS配置
    cors_origins: list[str] = ["*"]
    
    # 安全配置
    api_key: str = "your-api-key-here"
    
    # 监控配置
    prometheus_port: int = 9092
    metrics_enabled: bool = True
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

# 全局配置实例
settings = Settings()