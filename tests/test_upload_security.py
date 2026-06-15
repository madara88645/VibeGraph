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


def test_upload_corrupt_zip():
    """Ensure that corrupt zip files are handled gracefully."""
    zip_path = "corrupt.zip"

    # Write invalid zip data
    with open(zip_path, "wb") as f:
        f.write(b"Not a valid zip file content")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project",
            files={"files": ("corrupt.zip", f, "application/zip")},
        )

    # Clean up
    os.remove(zip_path)

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid zip archive detected."


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
    assert "No supported source files" in detail
    assert "Unsafe zip file detected" not in detail


def test_upload_too_many_multipart_files():
    """Ensure that uploading too many files directly via multipart is rejected."""
    # MAX_UPLOAD_FILES is 10000, so we create 10001 mock files
    # Note: Starlette has a built-in max_files default of 1000 which will reject this
    # with a 400 Bad Request before it reaches our endpoint logic, which is also
    # an acceptable and secure behavior.
    files = [
        ("files", (f"file_{i}.py", b"print('hello')", "text/x-python"))
        for i in range(1001)
    ]

    response = client.post("/api/upload-project", files=files)

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Too many files" in detail


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

    # With the new behavior, absolute paths inside zip files are explicitly rejected
    # instead of silently sanitized, so we *do* expect an "Unsafe zip file detected" error.
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Unsafe zip file detected" in detail


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


def test_upload_symlink_zip():
    """Ensure that zip files containing symbolic links are rejected."""
    import stat

    zip_path = "symlink_test.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        # Normal file
        z.writestr("normal.py", "print('hello')")
        # Symlink file (pointing to /etc/passwd)
        zinfo = zipfile.ZipInfo("symlink.txt")
        zinfo.create_system = 3  # Unix
        zinfo.external_attr = stat.S_IFLNK << 16
        z.writestr(zinfo, "/etc/passwd")

    with open(zip_path, "rb") as f:
        response = client.post(
            "/api/upload-project",
            files={"files": ("symlink_test.zip", f, "application/zip")},
        )

    # Clean up
    os.remove(zip_path)

    assert response.status_code == 400
    assert "Unsafe zip file detected" in response.json()["detail"]


def test_upload_extraction_error():
    """Ensure that an exception during zip extraction is caught and handled."""
    import io
    from unittest.mock import patch

    # Use io.BytesIO to avoid disk I/O
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("normal.py", "print('hello')")

    buf.seek(0)

    # Mock zipfile.ZipFile.open to raise BadZipFile during extraction
    with patch("zipfile.ZipFile.open") as mock_open:
        mock_open.side_effect = zipfile.BadZipFile("Corrupted file in zip")

        response = client.post(
            "/api/upload-project",
            files={"files": ("valid_test.zip", buf, "application/zip")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid zip archive detected."
