from fastapi.testclient import TestClient
from serve import app

client = TestClient(app)


def test_health_endpoint_post_405():
    response = client.post("/api/health")
    assert response.status_code == 405
