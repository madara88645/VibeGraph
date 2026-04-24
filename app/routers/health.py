"""Health check endpoint."""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.rate_limit import HEALTH_LIMIT, limiter

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    vibe: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
@limiter.limit(HEALTH_LIMIT)
def health(request: Request):
    """Basic health check."""
    return {"status": "ok", "vibe": "checked"}
