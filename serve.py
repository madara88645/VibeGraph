"""
Backward-compatible entry point for the VibeGraph API.

The application has been refactored into the `app/` package.
This module re-exports key symbols so existing imports continue to work:
    from serve import app, _is_safe_path, _extract_snippet, UPLOAD_PREFIX
"""

import uvicorn

from app import app  # noqa: F401
from app.utils.security import UPLOAD_PREFIX  # noqa: F401
from app.utils.security import is_safe_path as _is_safe_path  # noqa: F401
from app.utils.snippet import extract_snippet as _extract_snippet  # noqa: F401

import os

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
