import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "区块链集成服务"


def test_service_info():
    """测试服务信息端点"""
    response = client.get("/info")
    assert response.status_code == 200
    info = response.json()
    assert info["name"] == "区块链集成服务"
    assert info["version"] == "1.0.0"


def test_blockchain_status():
    """测试区块链状态端点"""
    response = client.get("/api/blockchain/status")
    assert response.status_code == 200
    assert "block_height" in response.json()
    assert "gas_price" in response.json()


def test_smart_contract():
    """测试智能合约端点"""
    response = client.get("/api/blockchain/contract")
    assert response.status_code == 404 or response.status_code == 200
    if response.status_code == 200:
        assert "contract" in response.json()
