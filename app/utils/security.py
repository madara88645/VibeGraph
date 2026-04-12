"""Path safety and file upload security utilities."""

import os
import re
import tempfile

from fastapi import HTTPException


HIDDEN_RE = re.compile(
    rf"(^|{re.escape(os.sep)})\.(?![{re.escape(os.sep)}]|$)", re.IGNORECASE
)

UPLOAD_PREFIX = "vibegraph_upload_"


def is_safe_path(path: str) -> bool:
    """Ensure the path is either within the current working directory or a valid upload temp directory."""
    try:
        resolved = os.path.realpath(path)
        cwd = os.path.realpath(os.getcwd())

        if os.path.commonpath([resolved, cwd]) == cwd:
            rel_path = os.path.relpath(resolved, cwd)
            # PERFORMANCE OPTIMIZATION (Bolt): Optimize hidden path segment check
            # by replacing the O(N) path split and generator expression with a fast
            # C-optimized regular expression search, which avoids unnecessary allocations.
            if HIDDEN_RE.search(rel_path):
                return False
            return True
    except ValueError:
        pass

    tmp_dir = os.path.realpath(tempfile.gettempdir())
    try:
        if os.path.commonpath([resolved, tmp_dir]) == tmp_dir:
            rel_path = os.path.relpath(resolved, tmp_dir)
            # PERFORMANCE OPTIMIZATION (Bolt): Optimize hidden path segment check
            # by replacing the O(N) path split and generator expression with a fast
            # C-optimized regular expression search, which avoids unnecessary allocations.
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

    # PERFORMANCE OPTIMIZATION (Bolt): Use a single split and generator
    # to avoid creating a new list if we encounter path traversal early.
    parts = []
    for p in normalized.split("/"):
        if p == "..":
            raise HTTPException(status_code=400, detail=f"Unsafe upload path: {raw_name}")
        if p not in ("", "."):
            parts.append(p)

    if not parts:
        raise HTTPException(status_code=400, detail=f"Invalid upload path: {raw_name}")

    safe_rel = "/".join(parts)
    if os.path.isabs(safe_rel):
        raise HTTPException(status_code=400, detail=f"Unsafe upload path: {raw_name}")

    return safe_rel
