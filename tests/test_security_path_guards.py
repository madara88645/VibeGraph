"""Direct unit tests for the private path-safety guards in app/utils/security.py.

These are exercised only indirectly today (via is_safe_path), so their own
boundary conditions — especially around path-traversal and sensitive-file
detection — have no direct assertions.
"""

import os

import pytest

from app.utils.security import _contains_sensitive_segment, _is_within_path


# ---------------------------------------------------------------------------
# _contains_sensitive_segment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel_path",
    [
        ".env",
        ".env.local",
        ".git",
        ".ssh",
        ".aws",
        ".npmrc",
        ".pypirc",
        ".netrc",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "identity",
        "certs/server.pem",
        "keys/private.key",
    ],
)
def test_contains_sensitive_segment_detects_known_sensitive_names(rel_path):
    assert _contains_sensitive_segment(rel_path) is True


def test_contains_sensitive_segment_detects_nested_sensitive_dir():
    assert _contains_sensitive_segment(os.path.join("project", ".git", "config")) is True


def test_contains_sensitive_segment_is_case_insensitive():
    assert _contains_sensitive_segment(".ENV") is True
    assert _contains_sensitive_segment("ID_RSA") is True
    assert _contains_sensitive_segment("SECRET.PEM") is True


def test_contains_sensitive_segment_handles_backslash_separators():
    assert _contains_sensitive_segment("project\\.git\\config") is True


@pytest.mark.parametrize(
    "rel_path",
    [
        "src/main.py",
        "README.md",
        "app/index.js",
        "environment.ts",  # starts with "environ", not ".env"
        "envelope.txt",
        "",
    ],
)
def test_contains_sensitive_segment_allows_benign_paths(rel_path):
    assert _contains_sensitive_segment(rel_path) is False


# ---------------------------------------------------------------------------
# _is_within_path
# ---------------------------------------------------------------------------


def test_is_within_path_true_for_direct_child():
    root = os.path.realpath("/tmp/vg_root")
    child = os.path.join(root, "sub", "file.txt")
    assert _is_within_path(child, root) is True


def test_is_within_path_true_for_root_itself():
    root = os.path.realpath("/tmp/vg_root")
    assert _is_within_path(root, root) is True


def test_is_within_path_false_for_sibling_path():
    root = os.path.realpath("/tmp/vg_root")
    sibling = os.path.realpath("/tmp/vg_root_evil")
    assert _is_within_path(sibling, root) is False


def test_is_within_path_false_for_parent_traversal():
    root = os.path.realpath("/tmp/vg_root/nested")
    traversal = os.path.realpath("/tmp/vg_root")
    assert _is_within_path(traversal, root) is False


def test_is_within_path_false_on_value_error(monkeypatch):
    def raise_value_error(_paths):
        raise ValueError("Paths don't have the same drive")

    monkeypatch.setattr(os.path, "commonpath", raise_value_error)
    assert _is_within_path("/tmp/a", "/tmp/b") is False
