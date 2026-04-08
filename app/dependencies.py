"""Shared dependencies and AI configuration helpers for the VibeGraph API."""

import os

from fastapi import HTTPException, Request

from analyst.exporter import GraphExporter
from teacher.openrouter_teacher import OpenRouterTeacher


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-haiku-4.5"
CURATED_MODELS = [
    "anthropic/claude-haiku-4.5",
    "google/gemini-2.5-flash-lite",
    "openai/gpt-5-mini",
    "deepseek/deepseek-chat-v3.1",
    "x-ai/grok-4.1-fast",
]

teacher = None
exporter = GraphExporter()


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_default_model() -> str:
    model_name = (os.getenv("OPENROUTER_DEFAULT_MODEL") or "").strip()
    return model_name or DEFAULT_OPENROUTER_MODEL


def get_allowed_models() -> list[str]:
    models: list[str] = []
    configured = (os.getenv("OPENROUTER_ALLOWED_MODELS") or "").split(",")
    for candidate in [get_default_model(), *CURATED_MODELS, *configured]:
        model_name = (candidate or "").strip()
        if model_name and model_name not in models:
            models.append(model_name)
    return models


def _get_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None
    cleaned = token.strip()
    return cleaned or None


def is_server_fallback_enabled() -> bool:
    if not _env_flag("ALLOW_SERVER_FALLBACK_KEY", default=False):
        return False
    return bool((os.getenv("OPENROUTER_API_KEY") or "").strip())


def get_public_ai_config() -> dict[str, object]:
    return {
        "provider": "openrouter",
        "defaultModel": get_default_model(),
        "allowedModels": get_allowed_models(),
        "requiresUserKey": not is_server_fallback_enabled(),
    }


def resolve_model_name(requested_model: str | None) -> str:
    model_name = (requested_model or "").strip() or get_default_model()
    allowed_models = get_allowed_models()
    if model_name not in allowed_models:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported model. "
                f"Allowed models: {', '.join(allowed_models)}"
            ),
        )
    return model_name


def resolve_openrouter_api_key(request: Request) -> str:
    bearer_token = _get_bearer_token(request)
    if bearer_token:
        return bearer_token

    if is_server_fallback_enabled():
        return os.getenv("OPENROUTER_API_KEY", "").strip()

    raise HTTPException(
        status_code=401,
        detail="OpenRouter API key required. Open AI Settings to continue.",
    )


def get_teacher_for_request(
    request: Request,
    requested_model: str | None = None,
):
    if teacher is not None:
        return teacher

    return OpenRouterTeacher(
        api_key=resolve_openrouter_api_key(request),
        model_name=resolve_model_name(requested_model),
        base_url=OPENROUTER_BASE_URL,
        http_referer=os.getenv("OPENROUTER_HTTP_REFERER"),
        app_title=os.getenv("OPENROUTER_APP_TITLE"),
    )
