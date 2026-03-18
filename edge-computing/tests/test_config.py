import pytest
from src.config.config import settings


def test_settings():
    """测试配置实例"""
    assert settings is not None
    assert settings.app_name == "边缘计算服务"
    assert settings.app_version == "1.0.0"
    assert settings.debug == True
    assert settings.host == "0.0.0.0"
    assert settings.port == 8002
    assert settings.edge_nodes == ["localhost:8080", "localhost:8081"]
    assert settings.task_queue_size == 1000
    assert settings.max_concurrent_tasks == 10
