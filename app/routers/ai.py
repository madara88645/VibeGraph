"""Routes for frontend AI configuration discovery."""

from fastapi import APIRouter

import app.dependencies as deps

router = APIRouter(prefix="/api", tags=["ai"])


@router.get("/ai-config", summary="Public AI provider configuration")
def get_ai_config():
    """Return safe frontend-facing AI configuration details."""
    return deps.get_public_ai_config()
