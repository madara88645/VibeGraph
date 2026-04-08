import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import app.dependencies as deps
from serve import app


client = TestClient(app)

CHAT_PAYLOAD = {
    "node_id": "main",
    "file_path": "tests/upload_cases/case_a.py",
    "question": "What does this function do?",
    "history": [],
}


def test_ai_config_reports_openrouter_defaults():
    with patch.dict(
        os.environ,
        {
            "OPENROUTER_DEFAULT_MODEL": "anthropic/claude-haiku-4.5",
            "OPENROUTER_ALLOWED_MODELS": "google/gemini-2.5-flash-lite,openai/gpt-5-mini",
            "ALLOW_SERVER_FALLBACK_KEY": "false",
        },
        clear=False,
    ):
        response = client.get("/api/ai-config")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openrouter"
    assert data["defaultModel"] == "anthropic/claude-haiku-4.5"
    assert "anthropic/claude-haiku-4.5" in data["allowedModels"]
    assert "google/gemini-2.5-flash-lite" in data["allowedModels"]
    assert "openai/gpt-5-mini" in data["allowedModels"]
    assert "deepseek/deepseek-chat-v3.1" in data["allowedModels"]
    assert "x-ai/grok-4.1-fast" in data["allowedModels"]
    assert data["requiresUserKey"] is True


def test_chat_requires_user_key_without_fallback(monkeypatch):
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "false")

    response = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert response.status_code == 401
    assert "OpenRouter API key" in response.json()["detail"]


def test_chat_rejects_unsupported_model(monkeypatch):
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "false")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-haiku-4.5")
    monkeypatch.setenv("OPENROUTER_ALLOWED_MODELS", "openai/gpt-5-mini")

    response = client.post(
        "/api/chat",
        json={**CHAT_PAYLOAD, "model": "not-allowed/model"},
        headers={"Authorization": "Bearer user-openrouter-key"},
    )

    assert response.status_code == 400
    assert "Unsupported model" in response.json()["detail"]


def test_chat_uses_bearer_key_and_selected_model(monkeypatch):
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "false")
    monkeypatch.setenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-haiku-4.5")
    monkeypatch.setenv(
        "OPENROUTER_ALLOWED_MODELS",
        "google/gemini-2.5-flash-lite,openai/gpt-5-mini",
    )

    with patch("app.dependencies.OpenRouterTeacher") as mock_teacher_cls:
        mock_teacher = MagicMock()
        mock_teacher.chat.return_value = "Configured answer"
        mock_teacher_cls.return_value = mock_teacher

        response = client.post(
            "/api/chat",
            json={**CHAT_PAYLOAD, "model": "openai/gpt-5-mini"},
            headers={"Authorization": "Bearer user-openrouter-key"},
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "Configured answer"
    mock_teacher_cls.assert_called_once()
    assert mock_teacher_cls.call_args.kwargs["api_key"] == "user-openrouter-key"
    assert mock_teacher_cls.call_args.kwargs["model_name"] == "openai/gpt-5-mini"


def test_chat_can_use_server_fallback_key(monkeypatch):
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "server-side-fallback-key")
    monkeypatch.setenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-haiku-4.5")
    monkeypatch.delenv("OPENROUTER_ALLOWED_MODELS", raising=False)

    with patch("app.dependencies.OpenRouterTeacher") as mock_teacher_cls:
        mock_teacher = MagicMock()
        mock_teacher.chat.return_value = "Fallback answer"
        mock_teacher_cls.return_value = mock_teacher

        response = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["answer"] == "Fallback answer"
    assert mock_teacher_cls.call_args.kwargs["api_key"] == "server-side-fallback-key"
