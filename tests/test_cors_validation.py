import os
from unittest.mock import patch

from app import create_app


@patch.dict(
    os.environ,
    {
        "VIBEGRAPH_CORS_ORIGINS": "http://localhost:5173, https://vibegraph.vercel.app, https://evil.com"
    },
)
@patch.dict(
    os.environ, {"VIBEGRAPH_ALLOWED_CORS_DOMAINS": "localhost, vibegraph.vercel.app"}
)
def test_cors_origins_with_allowed_domains():
    app = create_app()

    cors_middleware = next(
        (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"), None
    )
    assert cors_middleware is not None

    allowed_origins = cors_middleware.kwargs.get("allow_origins", [])

    assert "http://localhost:5173" in allowed_origins
    assert "https://vibegraph.vercel.app" in allowed_origins
    assert "https://evil.com" not in allowed_origins


@patch.dict(
    os.environ, {"VIBEGRAPH_CORS_ORIGINS": "http://localhost:5173, https://evil.com"}
)
def test_cors_origins_without_allowed_domains():
    app = create_app()

    cors_middleware = next(
        (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"), None
    )
    assert cors_middleware is not None

    allowed_origins = cors_middleware.kwargs.get("allow_origins", [])

    assert "http://localhost:5173" in allowed_origins
    assert "https://evil.com" in allowed_origins


@patch.dict(os.environ, {"VIBEGRAPH_CORS_ORIGINS": "*"})
@patch.dict(os.environ, {"VIBEGRAPH_ALLOWED_CORS_DOMAINS": "localhost"})
def test_cors_origins_wildcard_rejected_when_strictly_enforced():
    app = create_app()

    cors_middleware = next(
        (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"), None
    )
    assert cors_middleware is not None

    allowed_origins = cors_middleware.kwargs.get("allow_origins", [])

    assert "*" not in allowed_origins


@patch.dict(os.environ, {"VIBEGRAPH_CORS_ORIGINS": "*"})
def test_cors_origins_wildcard_allowed_without_strict_enforcement():
    if "VIBEGRAPH_ALLOWED_CORS_DOMAINS" in os.environ:
        del os.environ["VIBEGRAPH_ALLOWED_CORS_DOMAINS"]

    app = create_app()

    cors_middleware = next(
        (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"), None
    )
    assert cors_middleware is not None

    allowed_origins = cors_middleware.kwargs.get("allow_origins", [])

    assert "*" in allowed_origins
