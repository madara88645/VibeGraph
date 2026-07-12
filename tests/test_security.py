import pytest
import os
import tempfile
from fastapi import HTTPException
from unittest.mock import patch
from app.utils.security import normalize_uploaded_filename, is_safe_path


def test_is_safe_path_realpath_value_error():
    """Test is_safe_path returns False when os.path.realpath raises ValueError."""
    with patch("os.path.realpath") as mock_realpath:
        mock_realpath.side_effect = ValueError("Invalid path")
        assert is_safe_path("some/path") is False


def test_is_safe_path_commonpath_value_error():
    """Test is_safe_path returns False when os.path.commonpath raises ValueError."""
    # We need realpath to pass, but commonpath to fail.
    # We can patch just commonpath to raise ValueError.
    with patch("os.path.commonpath") as mock_commonpath:
        mock_commonpath.side_effect = ValueError("Paths are on different drives")
        assert is_safe_path("vibegraph_upload_123/file.txt") is False


def test_is_safe_path_allows_legitimate_hidden_project_dirs_in_uploads():
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    path = os.path.join(tmp_dir, ".storybook", "main.js")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("export function configure() {}\n")

    assert is_safe_path(path) is True


def test_is_safe_path_blocks_sensitive_hidden_files_in_uploads():
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    sensitive_paths = [
        os.path.join(tmp_dir, ".env"),
        os.path.join(tmp_dir, ".git", "config"),
        os.path.join(tmp_dir, ".ssh", "id_rsa"),
        os.path.join(tmp_dir, ".aws", "credentials"),
        os.path.join(tmp_dir, ".npmrc"),
    ]

    for path in sensitive_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("secret\n")
        assert is_safe_path(path) is False


def test_is_safe_path_allows_bundled_demo_project_sources():
    path = os.path.join("app", "demo_project", "api.py")

    assert is_safe_path(path) is True


def test_is_safe_path_blocks_sensitive_files_inside_demo_project():
    path = os.path.join("app", "demo_project", ".env")

    assert is_safe_path(path) is False


def test_normalize_uploaded_filename_valid():
    """Test valid uploaded filenames are correctly normalized."""
    assert normalize_uploaded_filename("foo/bar.py") == "foo/bar.py"
    assert normalize_uploaded_filename("bar.py") == "bar.py"
    assert normalize_uploaded_filename("a/b/c/d.py") == "a/b/c/d.py"

    # Test normalization of backslashes
    assert normalize_uploaded_filename("foo\\bar.py") == "foo/bar.py"

    # Test removal of empty parts and current directory dots
    assert normalize_uploaded_filename("foo/./bar.py") == "foo/bar.py"
    assert normalize_uploaded_filename("foo//bar.py") == "foo/bar.py"


def test_normalize_uploaded_filename_empty():
    """Test empty, missing, or invalid filenames."""
    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename(None)
    assert exc_info.value.status_code == 400
    assert "no filename" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("")
    assert exc_info.value.status_code == 400
    assert "no filename" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("/")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename(".")
    assert exc_info.value.status_code == 400
    assert "Invalid upload path" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("./.")
    assert exc_info.value.status_code == 400
    assert "Invalid upload path" in exc_info.value.detail


def test_normalize_uploaded_filename_traversal():
    """Test path traversal attempts are blocked."""
    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("../foo.py")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("foo/../../bar.py")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path" in exc_info.value.detail


def test_normalize_uploaded_filename_blocks_sensitive_hidden_names_case_insensitively():
    for raw_name in [
        ".ENV",
        ".Git/config",
        ".SSH/id_rsa",
        ".AWS/credentials",
        ".NPMRC",
        ".PyPiRc",
        ".NETRC",
    ]:
        with pytest.raises(HTTPException) as exc_info:
            normalize_uploaded_filename(raw_name)
        assert exc_info.value.status_code == 400
        assert "Sensitive hidden file or directory not allowed" in exc_info.value.detail


def test_normalize_uploaded_filename_absolute():
    """Test absolute paths are blocked."""
    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("/etc/passwd")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("/absolute/path/file.py")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path" in exc_info.value.detail


def test_normalize_uploaded_filename_blocks_env_variants():
    """Test that all .env variants are blocked by normalize_uploaded_filename."""
    variants = [
        ".env",
        ".env.local",
        ".env.development",
        ".env.production",
        ".env.test",
        ".env.custom",
        ".ENV.LOCAL",
        "subdir/.env.local",
        "subdir/.env.development",
    ]
    for raw_name in variants:
        with pytest.raises(HTTPException) as exc_info:
            normalize_uploaded_filename(raw_name)
        assert exc_info.value.status_code == 400
        assert "Sensitive hidden file or directory not allowed" in exc_info.value.detail


def test_is_safe_path_blocks_env_variants_in_uploads():
    """Test that is_safe_path blocks .env variants in temp directory uploads."""
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    variants = [
        ".env.local",
        ".env.development",
        ".env.production",
        ".env.test",
        ".ENV.LOCAL",
    ]
    for variant in variants:
        path = os.path.join(tmp_dir, variant)
        with open(path, "w", encoding="utf-8") as f:
            f.write("secret\n")
        assert is_safe_path(path) is False
