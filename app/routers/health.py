"""Health check endpoint."""

import os
import secrets

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.rate_limit import CHAT_LIMIT, limiter

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    vibe: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
@limiter.limit(CHAT_LIMIT)
def health(request: Request):
    """Basic health check."""
    expected_token = os.getenv("HEALTH_CHECK_TOKEN")
    auth_header = request.headers.get("Authorization")
    if not expected_token or not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authentication token",
        )

    expected_auth = f"Bearer {expected_token}"
    if not secrets.compare_digest(auth_header, expected_auth):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authentication token",
        )

    return {"status": "ok", "vibe": "checked"}
