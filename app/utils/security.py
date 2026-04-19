"""Path safety and file upload security utilities."""

import os
import tempfile

from fastapi import HTTPException


UPLOAD_PREFIX = "vibegraph_upload_"


def is_safe_path(path: str) -> bool:
    """Ensure the path is either within the current working directory or a valid upload temp directory."""
    try:
        resolved = os.path.realpath(path)
        cwd = os.path.realpath(os.getcwd())

        if os.path.commonpath([resolved, cwd]) == cwd:
            rel_path = os.path.relpath(resolved, cwd)
            parts = rel_path.split(os.sep)
            # Block hidden files and directories
            if any(part.startswith(".") for part in parts if part != "."):
                return False
            return True
    except ValueError:
        pass

    tmp_dir = os.path.realpath(tempfile.gettempdir())
    try:
        if os.path.commonpath([resolved, tmp_dir]) == tmp_dir:
            rel_path = os.path.relpath(resolved, tmp_dir)
            parts = rel_path.split(os.sep)
            # Block hidden files and directories
            if any(part.startswith(".") for part in parts if part != "."):
                return False
            if parts and (
                parts[0].startswith(UPLOAD_PREFIX)
                or parts[0].startswith("vibegraph_test_")
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

    safe_rel = "/".join(parts)
    if os.path.isabs(safe_rel):
        raise HTTPException(status_code=400, detail=f"Unsafe upload path: {raw_name}")

    return safe_rel
