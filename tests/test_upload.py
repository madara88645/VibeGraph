"""Upload integration tests — uses TestClient (no live server needed)."""

from fastapi.testclient import TestClient
from serve import app

client = TestClient(app)


def test_case_a_single_file():
    """Single .py file upload should return graph data."""
    file_path = "tests/upload_cases/case_a.py"
    with open(file_path, "rb") as f:
        files = {"files": ("case_a.py", f, "text/x-python")}
        response = client.post("/api/upload-project", files=files)

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
        response = client.post("/api/upload-project", files=files)
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
        response = client.post("/api/upload-project", files=files)

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}: {response.text}"
    )
    assert "Syntax error" in response.json()["detail"]
