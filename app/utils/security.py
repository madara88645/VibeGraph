"""Path safety and file upload security utilities."""

import os
import tempfile

from fastapi import HTTPException


UPLOAD_PREFIX = "vibegraph_upload_"

SENSITIVE_HIDDEN_SEGMENTS = frozenset(
    {
        ".env",
        ".git",
        ".ssh",
        ".aws",
        ".npmrc",
        ".pypirc",
        ".netrc",
    }
)
SENSITIVE_KEY_FILENAMES = frozenset(
    {"id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "identity"}
)


def _contains_sensitive_segment(rel_path: str) -> bool:
    parts = [part.lower() for part in rel_path.replace("\\", os.sep).split(os.sep)]
    for part in parts:
        if part in SENSITIVE_HIDDEN_SEGMENTS or part in SENSITIVE_KEY_FILENAMES:
            return True
        if part.endswith((".pem", ".key")):
            return True
    return False


def is_safe_path(path: str) -> bool:
    """Ensure the path is within a valid upload temp directory."""
    try:
        resolved = os.path.realpath(path)
    except ValueError:
        return False

    tmp_dir = os.path.realpath(tempfile.gettempdir())
    try:
        if os.path.commonpath([resolved, tmp_dir]) == tmp_dir:
            rel_path = os.path.relpath(resolved, tmp_dir)
            if _contains_sensitive_segment(rel_path):
                return False

            first_part = rel_path.partition(os.sep)[0]
            if first_part and (
                first_part.startswith(UPLOAD_PREFIX)
                or first_part.startswith("vibegraph_test_")
            ):
                return True
    except ValueError:
        pass

    return False


def normalize_uploaded_filename(raw_name: str | None) -> str:
    """Normalize upload path and block path traversal / absolute paths."""
    if not raw_name:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")

    normalized = raw_name.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if not parts:
        raise HTTPException(status_code=400, detail=f"Invalid upload path: {raw_name}")

    if ".." in parts:
        raise HTTPException(status_code=400, detail=f"Unsafe upload path: {raw_name}")

    sensitive_names = {".env", ".git", ".ssh", ".aws", ".npmrc", ".pypirc", ".netrc"}
    for part in parts:
        if part in sensitive_names:
            raise HTTPException(
                status_code=400,
                detail=f"Sensitive hidden file or directory not allowed: {part}",
            )

    safe_rel = "/".join(parts)
    if os.path.isabs(safe_rel):
        raise HTTPException(status_code=400, detail=f"Unsafe upload path: {raw_name}")

    return safe_rel
