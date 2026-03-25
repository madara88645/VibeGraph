"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    vibe: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
def health():
    """Basic health check."""
    return {"status": "ok", "vibe": "checked"}
