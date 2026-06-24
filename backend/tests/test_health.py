"""健康检查测试."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """测试客户端."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """测试健康检查接口."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data


def test_ping(client: TestClient) -> None:
    """测试 ping 接口."""
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
    assert response.json()["message"] == "pong"
