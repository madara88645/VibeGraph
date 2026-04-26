"""Upload integration tests — uses TestClient (no live server needed)."""

import os
import tempfile
import zipfile
from io import BytesIO
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


def test_upload_project_rejects_python_without_analyzable_code():
    """A .py upload with no functions/classes/calls should not be treated as a graph."""
    files = {"files": ("empty_module.py", BytesIO(b"ANSWER = 42\n"), "text/x-python")}
    response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 400
    assert "No analyzable Python code found" in response.json()["detail"]


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


def test_zip_with_non_utf8_file_returns_200_with_partial_graph():
    """A non-UTF-8 file in a zip must not crash the whole upload to 500.

    Regression guard for the encoding bug: previously one cp1252 file
    without a coding declaration raised UnicodeDecodeError out of the
    analyzer and the entire upload returned 500.
    """
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("proj/good.py", b"def alpha():\n    return 1\n")
        zf.writestr(
            "proj/legacy.py",
            b"# -*- coding: cp1252 -*-\ndef beta():\n    return 'caf\xe9'\n",
        )
        zf.writestr("proj/junk.py", b"def gamma():\n    return 'caf\xe9'\n")

    buffer.seek(0)
    files = {"files": ("proj.zip", buffer, "application/zip")}
    response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    node_ids = {node["id"] for node in data["nodes"]}
    assert "alpha" in node_ids
    assert "beta" in node_ids
    assert "gamma" not in node_ids
    # The skipped file must now be reported back to the user as a warning
    # so they know analysis was partial.
    warnings = data.get("warnings") or []
    assert any("junk.py" in w for w in warnings), (
        f"expected a warning mentioning junk.py, got {warnings}"
    )


def test_partial_success_multifile_returns_warnings():
    """Multi-file upload with a mix of good/bad files: 200 + warnings list.

    Previously, when a graph could be built from at least one file, every
    other failure was silently dropped from the response. The user saw a
    partial graph with no indication that some files were skipped.
    """
    good = BytesIO(b"def alpha():\n    return 1\n")
    bad_syntax = BytesIO(b"def broken(\n")
    # 1 MB + 1 byte: under the 50 MB upload cap, over the 1 MB analyzer cap.
    huge = BytesIO(b"x = 1\n" + b"# pad\n" * (1024 * 1024 // 6 + 1))

    files = [
        ("files", ("good.py", good, "text/x-python")),
        ("files", ("bad.py", bad_syntax, "text/x-python")),
        ("files", ("huge.py", huge, "text/x-python")),
    ]
    response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    node_ids = {node["id"] for node in data["nodes"]}
    assert "alpha" in node_ids

    warnings = data.get("warnings") or []
    assert any("bad.py" in w for w in warnings), (
        f"expected a warning mentioning bad.py, got {warnings}"
    )
    assert any("huge.py" in w for w in warnings), (
        f"expected a warning mentioning huge.py, got {warnings}"
    )


def test_all_fail_multifile_aggregates_errors():
    """When every uploaded file fails, the 400 detail must mention all of them.

    Previously only the first error was returned, forcing users to fix and
    re-upload N times.
    """
    bad_syntax = BytesIO(b"def broken(\n")
    bad_encoding = BytesIO(b"def b():\n    return 'caf\xe9'\n")

    files = [
        ("files", ("syntax_bad.py", bad_syntax, "text/x-python")),
        ("files", ("encoding_bad.py", bad_encoding, "text/x-python")),
    ]
    response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}: {response.text}"
    )
    detail = response.json().get("detail", "")
    assert "syntax_bad.py" in detail, (
        f"expected detail to mention syntax_bad.py, got {detail}"
    )
    assert "encoding_bad.py" in detail, (
        f"expected detail to mention encoding_bad.py, got {detail}"
    )


def test_same_basename_files_distinguished_in_warnings():
    """Two files named utils.py in different subpackages must be distinguishable.

    Errors used to be built from os.path.basename(file_path), so both
    pkg_a/utils.py and pkg_b/utils.py collapsed to "utils.py" in the message.
    """
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("pkg_a/utils.py", b"def a_helper():\n    return 1\n")
        zf.writestr("pkg_b/utils.py", b"def broken(\n")

    buffer.seek(0)
    files = {"files": ("proj.zip", buffer, "application/zip")}
    response = client.post("/api/upload-project", files=files, timeout=30.0)

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    data = response.json()
    warnings = data.get("warnings") or []
    assert any("pkg_b/utils.py" in w for w in warnings), (
        f"expected a warning naming pkg_b/utils.py specifically, got {warnings}"
    )
    assert not any(("pkg_a/utils.py" in w) for w in warnings), (
        f"pkg_a/utils.py is valid and should not appear in warnings: {warnings}"
    )


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
