import sys
import os
import pydantic
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from serve import app
from app.routers.health import HealthResponse

client = TestClient(app)


def test_health_get():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "vibe": "checked"}


def test_health_post_405():
    response = client.post("/api/health")
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


def test_health_with_auth_key_missing():
    os.environ["HEALTH_API_KEY"] = "secret123"
    try:
        response = client.get("/api/health")
        assert response.status_code == 401
    finally:
        del os.environ["HEALTH_API_KEY"]


def test_health_with_auth_key_valid():
    os.environ["HEALTH_API_KEY"] = "secret123"
    try:
        response = client.get(
            "/api/health", headers={"Authorization": "Bearer secret123"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "vibe": "checked"}
    finally:
        del os.environ["HEALTH_API_KEY"]
