"""Upload integration tests — uses TestClient (no live server needed)."""

import os
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.routers.upload import cleanup_tmp_dir
from serve import app

client = TestClient(app)


def test_case_a_single_file():
    """Single .py file upload should return graph data."""
    file_path = "tests/upload_cases/case_a.py"
    with open(file_path, "rb") as f:
        files = {"files": ("case_a.py", f, "text/x-python")}
        response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "nodes" in data


def test_case_b_multi_file():
    """Multi-file folder upload should detect cross-file calls."""
    f1 = open("tests/upload_cases/lib/core.py", "rb")
    f2 = open("tests/upload_cases/lib/utils.py", "rb")
    files = [
        ("files", ("lib/core.py", f1, "text/x-python")),
        ("files", ("lib/utils.py", f2, "text/x-python")),
    ]
    try:
        response = client.post("/api/upload-project", files=files, timeout=30.0)
    finally:
        f1.close()
        f2.close()

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    node_ids = [node["id"] for node in data["nodes"]]
    assert "run_lib" in node_ids
    assert "helper" in node_ids


def test_case_c_error_handling():
    """Invalid syntax file should return 400 with error detail."""
    file_path = "tests/upload_cases/invalid.py"
    with open(file_path, "rb") as f:
        files = {"files": ("invalid.py", f, "text/x-python")}
        response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}: {response.text}"
    )
    assert "Syntax error" in response.json()["detail"]


def test_cleanup_tmp_dir_success():
    """Test successful removal of an existing directory."""
    tmp_dir = tempfile.mkdtemp()
    assert os.path.exists(tmp_dir)

    cleanup_tmp_dir(tmp_dir)
    assert not os.path.exists(tmp_dir)


def test_cleanup_tmp_dir_not_exists():
    """Test cleanup when the directory does not exist."""
    fake_path = "/path/that/definitely/does/not/exist/12345"
    assert not os.path.exists(fake_path)

    # Should not raise any exceptions
    cleanup_tmp_dir(fake_path)


@patch("app.routers.upload.shutil.rmtree")
def test_cleanup_tmp_dir_calls_ignore_errors(mock_rmtree):
    """Test that cleanup_tmp_dir passes ignore_errors=True to shutil.rmtree."""
    tmp_dir = tempfile.mkdtemp()
    assert os.path.exists(tmp_dir)

    cleanup_tmp_dir(tmp_dir)

    mock_rmtree.assert_called_once_with(tmp_dir, ignore_errors=True)

    # Cleanup the actual temp dir since the mock prevented it
    os.rmdir(tmp_dir)


def test_upload_project_size_limit():
    """Test that an overly large set of files raises a 413 error."""
    # We will mock the file so we don't have to generate a 50MB file
    from io import BytesIO

    # 50MB + 1 byte
    large_content = b"x" * (50 * 1024 * 1024 + 1)

    files = {"files": ("large.py", BytesIO(large_content), "text/x-python")}
    response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 413
    assert "Upload too large" in response.json()["detail"]
