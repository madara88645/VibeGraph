import sys
import os
import pydantic
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from serve import app
from app.routers.health import HealthResponse

client = TestClient(app)


def test_health_get_authenticated(monkeypatch):
    monkeypatch.setenv("HEALTH_CHECK_TOKEN", "test-token")
    response = client.get("/api/health", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "vibe": "checked"}


def test_health_get_unauthenticated(monkeypatch):
    monkeypatch.setenv("HEALTH_CHECK_TOKEN", "test-token")
    response = client.get("/api/health")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing authentication token"


def test_health_get_invalid_token(monkeypatch):
    monkeypatch.setenv("HEALTH_CHECK_TOKEN", "test-token")
    response = client.get(
        "/api/health", headers={"Authorization": "Bearer wrong-token"}
    )
    assert response.status_code == 401


def test_health_post_405(monkeypatch):
    monkeypatch.setenv("HEALTH_CHECK_TOKEN", "test-token")
    response = client.post(
        "/api/health", headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 405


def test_health_response_schema():
    """Verify that the response model matches exactly what is expected."""
    # It must allow instantiation with required fields
    response = HealthResponse(status="ok", vibe="checked")
    assert response.status == "ok"
    assert response.vibe == "checked"

    # It must raise an error if required fields are missing
    with pytest.raises(pydantic.ValidationError):
        HealthResponse(status="ok")
