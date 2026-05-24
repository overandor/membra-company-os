"""Test health check endpoint."""
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_health.db")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_healthy():
    response = client.get("/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data


def test_readiness():
    response = client.get("/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
