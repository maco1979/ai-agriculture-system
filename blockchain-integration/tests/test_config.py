import pytest
from src.config.config import settings


def test_settings():
    """测试配置实例"""
    assert settings is not None
    assert settings.app_name == "区块链集成服务"
    assert settings.app_version == "1.0.0"
    assert settings.debug == True
    assert settings.host == "0.0.0.0"
    assert settings.port == 8003
    assert settings.blockchain_api_url == "https://api.blockchain.com/v3"
    assert settings.smart_contract_address is not None
    assert settings.blockchain_enabled == True
