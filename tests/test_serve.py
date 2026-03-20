from fastapi.testclient import TestClient
from serve import app, _is_safe_path

client = TestClient(app)


def test_health_endpoint_post_405():
    response = client.post("/api/health")
    assert response.status_code == 405


def test_is_safe_path_blocks_hidden_files():
    """Ensure _is_safe_path blocks access to hidden files/directories."""
    # Should block hidden files in cwd
    assert not _is_safe_path(".env")
    assert not _is_safe_path(".gitignore")

    # Should block hidden directories in cwd
    assert not _is_safe_path(".git/config")
    assert not _is_safe_path(".github/workflows/main.yml")

    # Should allow normal files in cwd
    assert _is_safe_path("serve.py")
    assert _is_safe_path("tests/test_serve.py")
