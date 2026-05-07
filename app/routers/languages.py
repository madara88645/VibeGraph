"""``/api/languages`` — discoverability for the multi-language pivot.

The frontend reads this on mount to render per-language icons in node
badges, drive the language filter, and (in the upload widget) tell the
user which files actually get analysed. Adding a new language plugin
under ``analyst/languages/`` automatically extends this response — no
endpoint edits required.
"""

from __future__ import annotations

from fastapi import APIRouter

from analyst.languages import all_languages

router = APIRouter(prefix="/api", tags=["languages"])


@router.get(
    "/languages",
    summary="List source languages VibeGraph can analyse",
)
def list_languages() -> dict:
    return {"languages": all_languages()}
