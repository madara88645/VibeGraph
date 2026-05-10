"""``/api/languages`` — discoverability for the multi-language pivot.

The frontend reads this on mount to render per-language icons in node
badges, drive the language filter, and (in the upload widget) tell the
user which files actually get analysed. Adding a new language plugin
under ``analyst/languages/`` automatically extends this response — no
endpoint edits required.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from analyst.languages import all_languages
from app.rate_limit import limiter, CHAT_LIMIT

router = APIRouter(prefix="/api", tags=["languages"])


@router.get(
    "/languages",
    summary="List source languages VibeGraph can analyse",
)
@limiter.limit(CHAT_LIMIT)
def list_languages(request: Request) -> dict:
    return {"languages": all_languages()}
