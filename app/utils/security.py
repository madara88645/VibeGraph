"""Path safety and file upload security utilities."""

import os
import re
import tempfile

from fastapi import HTTPException


UPLOAD_PREFIX = "vibegraph_upload_"

# Match any hidden segment (starts with a dot) except the current directory single dot (.)
HIDDEN_RE = re.compile(
    rf"(^|{re.escape(os.sep)})\.(?![{re.escape(os.sep)}]|$)", re.IGNORECASE
)


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
            # Block hidden files and directories
            if HIDDEN_RE.search(rel_path):
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

    sensitive_names = {".env", ".git", ".ssh", ".aws", ".config"}
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
