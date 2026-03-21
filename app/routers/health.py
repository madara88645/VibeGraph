"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    """Basic health check."""
    return {"status": "ok", "vibe": "checked"}
