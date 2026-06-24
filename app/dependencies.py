"""Shared dependencies and AI configuration helpers for the VibeGraph API."""

import os
from threading import Lock

from analyst.analyzer import MAX_FILE_SIZE
from fastapi import HTTPException, Request
from slowapi.util import get_remote_address

from analyst.exporter import GraphExporter
from app.ai_models import CURATED_MODELS, DEFAULT_OPENROUTER_MODEL
from app.services.trial_meter import TrialMeter
from teacher.openrouter_teacher import OpenRouterTeacher


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
DEFAULT_TRIAL_FREE_CALLS = 5
DEFAULT_TRIAL_GLOBAL_DAILY_CAP = 500
TRIAL_EXHAUSTED_MESSAGE = (
    "Free trial used up — add your own OpenRouter key in AI Settings."
)
TRIAL_GLOBAL_CAP_MESSAGE = (
    "Free trial is unavailable for today — add your own OpenRouter key in AI Settings."
)
GHOST_OWN_KEY_MESSAGE = (
    "Ghost Runner narration requires your own OpenRouter key in AI Settings."
)

teacher = None
exporter = GraphExporter()
_trial_meter: TrialMeter | None = None
_trial_meter_config: tuple[int, int] | None = None
_trial_meter_lock = Lock()


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_non_negative_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def get_trial_meter() -> TrialMeter:
    """Return the process-local meter for the current trial configuration."""
    global _trial_meter, _trial_meter_config

    config = (
        _env_non_negative_int("TRIAL_FREE_CALLS", DEFAULT_TRIAL_FREE_CALLS),
        _env_non_negative_int("TRIAL_GLOBAL_DAILY_CAP", DEFAULT_TRIAL_GLOBAL_DAILY_CAP),
    )
    with _trial_meter_lock:
        if _trial_meter is None or _trial_meter_config != config:
            _trial_meter = TrialMeter(
                free_calls=config[0],
                global_daily_cap=config[1],
            )
            _trial_meter_config = config
        return _trial_meter


def _reset_trial_meter() -> None:
    """Reset process-local trial state. Intended for isolated test setup."""
    global _trial_meter, _trial_meter_config
    with _trial_meter_lock:
        _trial_meter = None
        _trial_meter_config = None


def _get_trial_identity(request: Request) -> str:
    return get_remote_address(request)


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


def get_max_upload_bytes() -> int:
    raw_value = os.getenv("VIBEGRAPH_MAX_UPLOAD_BYTES", str(DEFAULT_MAX_UPLOAD_BYTES))
    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_UPLOAD_BYTES
    return parsed if parsed > 0 else DEFAULT_MAX_UPLOAD_BYTES


def get_public_upload_config() -> dict[str, int]:
    return {
        "maxTotalBytes": get_max_upload_bytes(),
        "maxPerFileBytes": MAX_FILE_SIZE,
    }


def get_public_ai_config(request: Request | None = None) -> dict[str, object]:
    trial_enabled = is_server_fallback_enabled()
    trial_remaining = 0
    if trial_enabled:
        identity = _get_trial_identity(request) if request is not None else "anonymous"
        trial_remaining = get_trial_meter().remaining(identity)

    return {
        "provider": "openrouter",
        "defaultModel": get_default_model(),
        "allowedModels": get_allowed_models(),
        "requiresUserKey": not trial_enabled or trial_remaining <= 0,
        "trialEnabled": trial_enabled,
        "trialRemaining": trial_remaining,
        "uploadLimits": get_public_upload_config(),
    }


def resolve_model_name(requested_model: str | None) -> str:
    model_name = (requested_model or "").strip() or get_default_model()
    allowed_models = get_allowed_models()
    if model_name not in allowed_models:
        raise HTTPException(
            status_code=400,
            detail=(f"Unsupported model. Allowed models: {', '.join(allowed_models)}"),
        )
    return model_name


def resolve_openrouter_api_key(
    request: Request,
    *,
    allow_server_trial: bool = True,
) -> str:
    bearer_token = _get_bearer_token(request)
    if bearer_token:
        return bearer_token

    if is_server_fallback_enabled():
        if not allow_server_trial:
            raise HTTPException(status_code=401, detail=GHOST_OWN_KEY_MESSAGE)

        meter = get_trial_meter()
        identity = _get_trial_identity(request)
        allowed, remaining = meter.consume_if_available(identity)
        if not allowed:
            request.state.trial_remaining = 0
            message = (
                TRIAL_GLOBAL_CAP_MESSAGE
                if meter.is_global_exhausted()
                else TRIAL_EXHAUSTED_MESSAGE
            )
            raise HTTPException(
                status_code=402,
                detail=message,
                headers={"X-Trial-Remaining": "0"},
            )

        request.state.trial_remaining = remaining
        return os.getenv("OPENROUTER_API_KEY", "").strip()

    raise HTTPException(
        status_code=401,
        detail="OpenRouter API key required. Open AI Settings to continue.",
    )


def get_teacher_for_request(
    request: Request,
    requested_model: str | None = None,
    *,
    allow_server_trial: bool = True,
):
    if teacher is not None:
        return teacher

    return OpenRouterTeacher(
        api_key=resolve_openrouter_api_key(
            request,
            allow_server_trial=allow_server_trial,
        ),
        model_name=resolve_model_name(requested_model),
        base_url=OPENROUTER_BASE_URL,
        http_referer=os.getenv(
            "OPENROUTER_HTTP_REFERER", "https://vibegraph.vercel.app"
        ),
        app_title=os.getenv("OPENROUTER_APP_TITLE", "VibeGraph"),
    )
