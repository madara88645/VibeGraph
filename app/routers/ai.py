"""Routes for frontend AI configuration discovery."""

from fastapi import APIRouter, Request

import app.dependencies as deps
from app.rate_limit import CHAT_LIMIT, limiter

router = APIRouter(prefix="/api", tags=["ai"])


@router.get("/ai-config", summary="Public AI provider configuration")
@limiter.limit(CHAT_LIMIT)
def get_ai_config(request: Request):
    """Return safe frontend-facing AI configuration details."""
    return deps.get_public_ai_config()
