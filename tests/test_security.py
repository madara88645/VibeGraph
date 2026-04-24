import pytest
from fastapi import HTTPException
from app.utils.security import normalize_uploaded_filename


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
    assert "Invalid upload path" in exc_info.value.detail

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


def test_normalize_uploaded_filename_hidden():
    """Test that hidden files and directories are blocked."""
    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename(".env")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path (hidden file)" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename("foo/.git/config")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path (hidden file)" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info:
        normalize_uploaded_filename(".hidden_dir/foo.py")
    assert exc_info.value.status_code == 400
    assert "Unsafe upload path (hidden file)" in exc_info.value.detail


def test_normalize_uploaded_filename_absolute():
    """Test absolute paths are converted or blocked.
    Because empty strings are filtered out by split('/'),
    an absolute path like '/etc/passwd' becomes ['etc', 'passwd'],
    which is considered a valid relative path 'etc/passwd' and returned.
    This effectively converts absolute paths to relative paths.
    """
    assert normalize_uploaded_filename("/etc/passwd") == "etc/passwd"
    assert (
        normalize_uploaded_filename("/absolute/path/file.py") == "absolute/path/file.py"
    )
