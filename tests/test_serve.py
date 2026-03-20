import pytest
from fastapi.testclient import TestClient
from serve import app, _is_safe_path

client = TestClient(app, raise_server_exceptions=False)


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


from unittest.mock import patch
from io import BytesIO


def test_upload_project_internal_error_leak():
    """Ensure internal errors during upload do not leak stack traces."""
    with patch(
        "serve.CodeAnalyzer.analyze_file",
        side_effect=Exception("SECRET_INTERNAL_ERROR"),
    ):
        file_content = b"print('hello')"
        files = {"files": ("test.py", BytesIO(file_content), "text/x-python")}
        response = client.post("/api/upload-project", files=files)

        assert response.status_code == 500
        assert "SECRET_INTERNAL_ERROR" not in response.text
        assert "Upload/Analysis failed due to an internal error." in response.text


def test_global_exception_handler_leak():
    """Ensure global unhandled exceptions return a generic 500 response."""
    with patch(
        "serve._extract_snippet", side_effect=Exception("SECRET_UNHANDLED_ERROR")
    ):
        try:
            response = client.post(
                "/api/snippet", json={"node_id": "test", "file_path": "test.py"}
            )
        except Exception as e:
            response = None
            pytest.fail(f"Exception propagated: {e}")

        assert response.status_code == 500
        assert "SECRET_UNHANDLED_ERROR" not in response.text
        assert response.status_code == 500
