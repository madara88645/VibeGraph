"""VibeGraph FastAPI application factory."""

import json
import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.routers import chat, explain, health, learning, upload

logger = logging.getLogger(__name__)


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
        return json.dumps(log_entry)


def configure_logging() -> None:
    """Set up structured JSON logging for production."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if root.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000)

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s %s %dms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"request_id": request_id},
        )
        return response


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()

    application = FastAPI(
        title="VibeGraph API",
        version="1.0.0",
        description=(
            "VibeGraph transforms Python codebases into interactive call graphs "
            "and provides AI-powered explanations, chat, and learning paths via Groq LLM."
        ),
        contact={"name": "VibeGraph", "url": "https://github.com/madara88645/VibeGraph"},
        license_info={"name": "MIT"},
    )

    # Request ID tracing
    application.add_middleware(RequestIDMiddleware)

    # Security headers
    application.add_middleware(SecurityHeadersMiddleware)

    # CORS
    cors_origins = os.getenv(
        "VIBEGRAPH_CORS_ORIGINS", "http://localhost:5173,http://localhost:8000"
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Global exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Catch-all to prevent leaking stack traces to the client."""
        logger.error(
            f"Unhandled exception during {request.method} {request.url.path}: {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Register routers
    application.include_router(health.router)
    application.include_router(explain.router)
    application.include_router(chat.router)
    application.include_router(learning.router)
    application.include_router(upload.router)

    # Mount static files (Frontend build)
    static_dir = os.path.join("explorer", "dist")
    if os.path.exists(static_dir):
        application.mount(
            "/", StaticFiles(directory=static_dir, html=True), name="static"
        )

    return application


app = create_app()
