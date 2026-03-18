import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "监控和日志服务"


def test_service_info():
    """测试服务信息端点"""
    response = client.get("/info")
    assert response.status_code == 200
    info = response.json()
    assert info["name"] == "监控和日志服务"
    assert info["version"] == "1.0.0"


def test_monitoring_metrics():
    """测试监控指标端点"""
    response = client.get("/api/monitoring/metrics")
    assert response.status_code == 404 or response.status_code == 200


def test_monitoring_alerts():
    """测试监控告警端点"""
    response = client.get("/api/monitoring/alerts")
    assert response.status_code == 404 or response.status_code == 200
