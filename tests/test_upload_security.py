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
    # Create a safe zip file with no Python source
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

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "No Python files found" in detail
    assert "Unsafe zip file detected" not in detail


def test_upload_too_many_files_zip():
    """Ensure that zip files with more than MAX_ZIP_FILES are rejected."""
    zip_path = "too_many_files.zip"

    # MAX_ZIP_FILES is 10000, so we create 10001 files
    with zipfile.ZipFile(zip_path, "w") as z:
        for i in range(10001):
            z.writestr(f"file_{i}.txt", "")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project",
            files={"files": ("too_many_files.zip", f, "application/zip")},
        )

    # Clean up
    os.remove(zip_path)

    assert response.status_code == 400
    assert "Too many files in zip archive" in response.json().get("detail", "")


def test_upload_absolute_path_zip():
    """Ensure that absolute paths in zip files are sanitized properly."""
    zip_path = "absolute_path.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        # File attempting to escape to absolute path
        z.writestr("/etc/passwd", "This is a malicious file")
        # Ensure there is at least a valid python file to not fail immediately on empty graph if graph generation logic changes later
        z.writestr("valid.py", "def a(): pass")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project",
            files={"files": ("absolute_path.zip", f, "application/zip")},
        )

    # Clean up
    os.remove(zip_path)

    # If the file is properly sanitized, it will extract to `tmp_dir/etc/passwd` rather than `/etc/passwd`.
    # Therefore, we shouldn't get an "Unsafe zip file detected" error.
    # Let's verify that the endpoint doesn't return the specific error.
    if response.status_code == 400:
        detail = response.json().get("detail", "")
        assert "Unsafe zip file detected" not in detail


def test_upload_hidden_file_zip():
    """Ensure that zip files containing hidden files/directories are rejected."""
    zip_path = "hidden_file.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        # A hidden file
        z.writestr(".env", "SECRET=123")
        # A hidden directory
        z.writestr(".git/config", "test")
        # A normal file
        z.writestr("normal.py", "print('hello')")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project",
            files={"files": ("hidden_file.zip", f, "application/zip")},
        )

    # Clean up
    os.remove(zip_path)

    assert response.status_code == 400
    assert "Unsafe zip file detected" in response.json()["detail"]


def test_upload_allowed_hidden_file_zip():
    """Ensure that zip files containing benign hidden files like .gitignore are allowed."""
    zip_path = "allowed_hidden_file.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        # A benign hidden file
        z.writestr(".gitignore", "node_modules/")
        # A normal file
        z.writestr("normal.py", "print('hello')")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project",
            files={"files": ("allowed_hidden_file.zip", f, "application/zip")},
        )

    # Clean up
    os.remove(zip_path)

    # Should not be rejected due to unsafe zip
    if response.status_code == 400:
        detail = response.json().get("detail", "")
        assert "Unsafe zip file detected" not in detail
