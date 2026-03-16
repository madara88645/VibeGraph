import os
import zipfile
from fastapi.testclient import TestClient
from serve import app

client = TestClient(app)


def test_upload_zip_slip():
    # Create a malicious zip file
    zip_path = "malicious.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        # A file attempting to write outside the temp directory
        z.writestr("../evil.txt", "This is a malicious file")
        # A normal file
        z.writestr("normal.txt", "This is a normal file")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project",
            files={"files": ("malicious.zip", f, "application/zip")},
        )

    # Clean up
    os.remove(zip_path)

    assert response.status_code == 400
    assert "Unsafe zip file detected" in response.json()["detail"]


def test_upload_safe_zip():
    # Create a safe zip file
    zip_path = "safe.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("dir/file1.txt", "Normal file 1")
        z.writestr("file2.txt", "Normal file 2")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project", files={"files": ("safe.zip", f, "application/zip")}
        )

    # Clean up
    os.remove(zip_path)

    # In this mock case, analysis might fail because there are no python files,
    # but it shouldn't fail with "Unsafe zip file detected" 400 error.
    # It might return 400 with "No Python files found" or similar if the analyzer
    # rejects it. Let's just check it doesn't return the unsafe zip error.
    if response.status_code == 400:
        detail = response.json().get("detail", "")
        assert "Unsafe zip file detected" not in detail
    else:
        assert response.status_code == 200


def test_hidden_file_access_blocked():
    """Test that the backend blocks access to hidden files like .env."""
    response = client.post(
        "/api/snippet", json={"file_path": ".env", "node_id": "test"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "Access denied: Unsafe file path" in data["snippet"]
    assert data["full_source"] is None
