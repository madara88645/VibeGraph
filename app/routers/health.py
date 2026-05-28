"""Health check endpoint."""

import os
import secrets

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from app.rate_limit import CHAT_LIMIT, limiter
import app.dependencies as deps

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    vibe: str


def verify_health_api_key(request: Request):
    api_key = os.getenv("HEALTH_API_KEY")
    if not api_key:
        return

    bearer = deps.get_bearer_token(request)
    if not bearer or not secrets.compare_digest(bearer, api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authentication token.",
        )


@router.get("/health", response_model=HealthResponse, summary="Health check")
@limiter.limit(CHAT_LIMIT)
def health(request: Request, _=Depends(verify_health_api_key)):
    """Basic health check."""
    return {"status": "ok", "vibe": "checked"}
