import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request, HTTPException

from app.dependencies import (
    _env_flag,
    get_default_model,
    get_allowed_models,
    _get_bearer_token,
    is_server_fallback_enabled,
    get_public_ai_config,
    get_trial_meter,
    resolve_model_name,
    resolve_openrouter_api_key,
    get_teacher_for_request,
    _reset_trial_meter,
    DEFAULT_OPENROUTER_MODEL,
    CURATED_MODELS,
)


def test_env_flag():
    with patch.dict(
        os.environ,
        {
            "TEST_FLAG_TRUE": "true",
            "TEST_FLAG_1": "1",
            "TEST_FLAG_YES": "yes",
            "TEST_FLAG_FALSE": "false",
            "TEST_FLAG_OFF": "off",
        },
        clear=True,
    ):
        assert _env_flag("TEST_FLAG_TRUE") is True
        assert _env_flag("TEST_FLAG_1") is True
        assert _env_flag("TEST_FLAG_YES") is True
        assert _env_flag("TEST_FLAG_FALSE") is False
        assert _env_flag("TEST_FLAG_OFF") is False
        assert _env_flag("NONEXISTENT_FLAG") is False
        assert _env_flag("NONEXISTENT_FLAG", default=True) is True


def test_get_default_model():
    with patch.dict(os.environ, {}, clear=True):
        assert get_default_model() == DEFAULT_OPENROUTER_MODEL

    with patch.dict(
        os.environ, {"OPENROUTER_DEFAULT_MODEL": "custom-model"}, clear=True
    ):
        assert get_default_model() == "custom-model"


def test_get_allowed_models():
    with patch.dict(os.environ, {}, clear=True):
        allowed = get_allowed_models()
        assert DEFAULT_OPENROUTER_MODEL in allowed
        for m in CURATED_MODELS:
            assert m in allowed

    with patch.dict(
        os.environ,
        {"OPENROUTER_ALLOWED_MODELS": "custom-model1,custom-model2"},
        clear=True,
    ):
        allowed = get_allowed_models()
        assert "custom-model1" in allowed
        assert "custom-model2" in allowed


def test_get_bearer_token():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer my-token"}
    assert _get_bearer_token(request) == "my-token"

    request.headers = {"Authorization": "bearer lower-token"}
    assert _get_bearer_token(request) == "lower-token"

    request.headers = {"Authorization": "Basic something"}
    assert _get_bearer_token(request) is None

    request.headers = {}
    assert _get_bearer_token(request) is None


def test_is_server_fallback_enabled():
    with patch.dict(os.environ, {}, clear=True):
        assert is_server_fallback_enabled() is False

    with patch.dict(os.environ, {"ALLOW_SERVER_FALLBACK_KEY": "true"}, clear=True):
        assert is_server_fallback_enabled() is False

    with patch.dict(
        os.environ,
        {"ALLOW_SERVER_FALLBACK_KEY": "true", "OPENROUTER_API_KEY": "some-key"},
        clear=True,
    ):
        assert is_server_fallback_enabled() is True


def test_get_public_ai_config():
    _reset_trial_meter()
    with patch.dict(
        os.environ,
        {"ALLOW_SERVER_FALLBACK_KEY": "true", "OPENROUTER_API_KEY": "some-key"},
        clear=True,
    ):
        config = get_public_ai_config()
        assert config["provider"] == "openrouter"
        assert config["defaultModel"] == get_default_model()
        assert config["allowedModels"] == get_allowed_models()
        assert config["requiresUserKey"] is False
        assert config["trialEnabled"] is True
        assert config["trialRemaining"] == 5

    with patch.dict(os.environ, {}, clear=True):
        config = get_public_ai_config()
        assert config["requiresUserKey"] is True
        assert config["trialEnabled"] is False
        assert config["trialRemaining"] == 0


def test_resolve_model_name():
    with patch.dict(os.environ, {}, clear=True):
        assert resolve_model_name(None) == DEFAULT_OPENROUTER_MODEL
        assert resolve_model_name("") == DEFAULT_OPENROUTER_MODEL
        assert resolve_model_name(CURATED_MODELS[1]) == CURATED_MODELS[1]

        with pytest.raises(HTTPException) as exc_info:
            resolve_model_name("unsupported-model")
        assert exc_info.value.status_code == 400
        assert "Unsupported model" in exc_info.value.detail


def test_resolve_openrouter_api_key():
    _reset_trial_meter()
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer request-token"}

    with patch.dict(os.environ, {}, clear=True):
        assert resolve_openrouter_api_key(request) == "request-token"

    request.headers = {}
    with patch.dict(
        os.environ,
        {"ALLOW_SERVER_FALLBACK_KEY": "true", "OPENROUTER_API_KEY": "env-key"},
        clear=True,
    ):
        assert resolve_openrouter_api_key(request) == "env-key"

    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(HTTPException) as exc_info:
            resolve_openrouter_api_key(request)
        assert exc_info.value.status_code == 401
        assert "OpenRouter API key required" in exc_info.value.detail


def test_resolve_openrouter_api_key_meters_server_trial_and_blocks_next_call():
    _reset_trial_meter()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/explain",
            "headers": [],
            "client": ("203.0.113.10", 1234),
        }
    )

    with patch.dict(
        os.environ,
        {
            "ALLOW_SERVER_FALLBACK_KEY": "true",
            "OPENROUTER_API_KEY": "env-key",
            "TRIAL_FREE_CALLS": "2",
            "TRIAL_GLOBAL_DAILY_CAP": "10",
        },
        clear=True,
    ):
        assert resolve_openrouter_api_key(request) == "env-key"
        assert request.state.trial_remaining == 1
        assert resolve_openrouter_api_key(request) == "env-key"
        assert request.state.trial_remaining == 0

        with pytest.raises(HTTPException) as exc_info:
            resolve_openrouter_api_key(request)

    assert exc_info.value.status_code == 402
    assert "Free trial used up" in exc_info.value.detail
    assert exc_info.value.headers == {"X-Trial-Remaining": "0"}


def test_resolve_openrouter_api_key_never_meters_bearer_key():
    _reset_trial_meter()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/explain",
            "headers": [(b"authorization", b"Bearer user-key")],
            "client": ("203.0.113.11", 1234),
        }
    )

    with patch.dict(
        os.environ,
        {
            "ALLOW_SERVER_FALLBACK_KEY": "true",
            "OPENROUTER_API_KEY": "env-key",
            "TRIAL_FREE_CALLS": "2",
            "TRIAL_GLOBAL_DAILY_CAP": "10",
        },
        clear=True,
    ):
        assert resolve_openrouter_api_key(request) == "user-key"
        assert resolve_openrouter_api_key(request) == "user-key"
        assert get_trial_meter().remaining("203.0.113.11") == 2


def test_resolve_openrouter_api_key_requires_own_key_for_ghost():
    _reset_trial_meter()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/ghost-narrate",
            "headers": [],
            "client": ("203.0.113.12", 1234),
        }
    )

    with patch.dict(
        os.environ,
        {
            "ALLOW_SERVER_FALLBACK_KEY": "true",
            "OPENROUTER_API_KEY": "env-key",
        },
        clear=True,
    ):
        with pytest.raises(HTTPException) as exc_info:
            resolve_openrouter_api_key(request, allow_server_trial=False)

    assert exc_info.value.status_code == 401
    assert "Ghost Runner narration requires your own" in exc_info.value.detail


def test_get_teacher_for_request():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer request-token"}

    with patch("app.dependencies.teacher", None):
        teacher = get_teacher_for_request(request)
        assert teacher is not None
        assert teacher.model_name == DEFAULT_OPENROUTER_MODEL

    with patch("app.dependencies.teacher", "singleton-teacher"):
        teacher = get_teacher_for_request(request)
        assert teacher == "singleton-teacher"
