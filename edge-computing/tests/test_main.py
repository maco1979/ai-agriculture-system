import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "边缘计算服务"


def test_service_info():
    """测试服务信息端点"""
    response = client.get("/info")
    assert response.status_code == 200
    info = response.json()
    assert info["name"] == "边缘计算服务"
    assert info["version"] == "1.0.0"


def test_edge_nodes():
    """测试获取边缘节点列表"""
    response = client.get("/api/edge/nodes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_edge_tasks():
    """测试获取边缘任务列表"""
    response = client.get("/api/edge/tasks")
    assert response.status_code == 405 or response.status_code == 200
    if response.status_code == 200:
        assert isinstance(response.json(), list)
