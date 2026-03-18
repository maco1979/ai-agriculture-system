import pytest
from src.config.config import settings


def test_settings():
    """测试配置实例"""
    assert settings is not None
    assert settings.app_name == "监控和日志服务"
    assert settings.app_version == "1.0.0"
    assert settings.debug == True
    assert settings.host == "0.0.0.0"
    assert settings.port == 8004
    assert settings.monitoring_enabled == True
    assert settings.prometheus_port == 9090
