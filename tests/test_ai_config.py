import os
import tempfile
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import app.dependencies as deps
from serve import app


client = TestClient(app)


def _make_temp_py(content: str = "def main(): pass") -> str:
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    path = os.path.join(tmp_dir, "case_a.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


test_file_path = _make_temp_py()

CHAT_PAYLOAD = {
    "node_id": "main",
    "file_path": test_file_path,
    "question": "What does this function do?",
    "history": [],
}


def test_ai_config_reports_openrouter_defaults():
    deps._reset_trial_meter()
    with patch.dict(
        os.environ,
        {
            "OPENROUTER_DEFAULT_MODEL": "deepseek/deepseek-v4-flash",
            "OPENROUTER_ALLOWED_MODELS": "google/gemini-3.1-flash-lite,anthropic/claude-sonnet-4.6",
            "ALLOW_SERVER_FALLBACK_KEY": "false",
            "VIBEGRAPH_MAX_UPLOAD_BYTES": str(25 * 1024 * 1024),
        },
        clear=False,
    ):
        response = client.get("/api/ai-config")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openrouter"
    assert data["defaultModel"] == "deepseek/deepseek-v4-flash"
    assert "deepseek/deepseek-v4-flash" in data["allowedModels"]
    assert "google/gemini-3.1-flash-lite" in data["allowedModels"]
    assert "anthropic/claude-sonnet-4.6" in data["allowedModels"]
    assert "qwen/qwen3-coder-30b-a3b-instruct" in data["allowedModels"]
    assert "meta-llama/llama-3.3-70b-instruct:free" not in data["allowedModels"]
    assert data["requiresUserKey"] is True
    assert data["trialEnabled"] is False
    assert data["trialRemaining"] == 0
    assert data["uploadLimits"]["maxTotalBytes"] == 25 * 1024 * 1024
    assert data["uploadLimits"]["maxPerFileBytes"] == 1024 * 1024


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
    monkeypatch.setenv("OPENROUTER_DEFAULT_MODEL", "deepseek/deepseek-v4-flash")
    monkeypatch.setenv("OPENROUTER_ALLOWED_MODELS", "anthropic/claude-sonnet-4.6")

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
    monkeypatch.setenv("OPENROUTER_DEFAULT_MODEL", "deepseek/deepseek-v4-flash")
    monkeypatch.setenv(
        "OPENROUTER_ALLOWED_MODELS",
        "google/gemini-3.1-flash-lite,anthropic/claude-sonnet-4.6",
    )

    with patch("app.dependencies.OpenRouterTeacher") as mock_teacher_cls:
        mock_teacher = MagicMock()
        mock_teacher.chat.return_value = "Configured answer"
        mock_teacher_cls.return_value = mock_teacher

        response = client.post(
            "/api/chat",
            json={**CHAT_PAYLOAD, "model": "anthropic/claude-sonnet-4.6"},
            headers={"Authorization": "Bearer user-openrouter-key"},
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "Configured answer"
    mock_teacher_cls.assert_called_once()
    assert mock_teacher_cls.call_args.kwargs["api_key"] == "user-openrouter-key"
    assert (
        mock_teacher_cls.call_args.kwargs["model_name"] == "anthropic/claude-sonnet-4.6"
    )


def test_chat_can_use_server_fallback_key(monkeypatch):
    deps._reset_trial_meter()
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "server-side-fallback-key")
    monkeypatch.setenv("OPENROUTER_DEFAULT_MODEL", "deepseek/deepseek-v4-flash")
    monkeypatch.delenv("OPENROUTER_ALLOWED_MODELS", raising=False)

    with patch("app.dependencies.OpenRouterTeacher") as mock_teacher_cls:
        mock_teacher = MagicMock()
        mock_teacher.chat.return_value = "Fallback answer"
        mock_teacher_cls.return_value = mock_teacher

        response = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["answer"] == "Fallback answer"
    assert mock_teacher_cls.call_args.kwargs["api_key"] == "server-side-fallback-key"


def test_server_trial_counts_ai_actions_across_routes_and_blocks_the_sixth(
    monkeypatch,
):
    deps._reset_trial_meter()
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "server-side-fallback-key")
    monkeypatch.setenv("TRIAL_FREE_CALLS", "5")
    monkeypatch.setenv("TRIAL_GLOBAL_DAILY_CAP", "50")

    mock_teacher = MagicMock()
    mock_teacher.explain_code.return_value = {
        "analogy": "Analogy",
        "technical": "Technical",
        "key_takeaway": "Takeaway",
    }
    mock_teacher.chat.return_value = "Fallback answer"
    mock_teacher.refine_learning_path.side_effect = lambda window, allowed_node_ids: (
        window
    )

    learning_payload = {
        "nodes": [
            {
                "id": "main",
                "data": {
                    "label": "main",
                    "file": "repo/main.py",
                    "type": "function",
                    "entry_point": True,
                    "lineno": 1,
                },
            }
        ],
        "edges": [],
        "selected_file": "repo/main.py",
    }
    actions = [
        ("/api/explain", {"file_path": test_file_path, "node_id": "main"}),
        ("/api/chat", CHAT_PAYLOAD),
        ("/api/learning-path", learning_payload),
        ("/api/explain", {"file_path": test_file_path, "node_id": "main"}),
        ("/api/chat", CHAT_PAYLOAD),
    ]

    with patch("app.dependencies.OpenRouterTeacher", return_value=mock_teacher):
        for expected_remaining, (path, payload) in zip(
            [4, 3, 2, 1, 0], actions, strict=True
        ):
            response = client.post(path, json=payload)
            assert response.status_code == 200
            assert response.headers["X-Trial-Remaining"] == str(expected_remaining)

        blocked = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert blocked.status_code == 402
    assert blocked.headers["X-Trial-Remaining"] == "0"
    assert "Free trial used up" in blocked.json()["detail"]

    config = client.get("/api/ai-config").json()
    assert config["trialEnabled"] is True
    assert config["trialRemaining"] == 0
    assert config["requiresUserKey"] is True


def test_server_trial_never_meters_user_key(monkeypatch):
    deps._reset_trial_meter()
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "server-side-fallback-key")
    monkeypatch.setenv("TRIAL_FREE_CALLS", "5")
    monkeypatch.setenv("TRIAL_GLOBAL_DAILY_CAP", "50")

    with patch("app.dependencies.OpenRouterTeacher") as mock_teacher_cls:
        mock_teacher = MagicMock()
        mock_teacher.chat.return_value = "User-funded answer"
        mock_teacher_cls.return_value = mock_teacher

        response = client.post(
            "/api/chat",
            json=CHAT_PAYLOAD,
            headers={"Authorization": "Bearer user-openrouter-key"},
        )

    assert response.status_code == 200
    assert "X-Trial-Remaining" not in response.headers
    config = client.get("/api/ai-config").json()
    assert config["trialRemaining"] == 5


def test_ghost_narration_requires_own_key_without_consuming_trial(monkeypatch):
    deps._reset_trial_meter()
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "server-side-fallback-key")
    monkeypatch.setenv("TRIAL_FREE_CALLS", "5")
    monkeypatch.setenv("TRIAL_GLOBAL_DAILY_CAP", "50")

    response = client.post(
        "/api/ghost-narrate",
        json={"file_path": test_file_path, "node_id": "main"},
    )

    assert response.status_code == 401
    assert "requires your own OpenRouter key" in response.json()["detail"]
    assert client.get("/api/ai-config").json()["trialRemaining"] == 5


def test_global_trial_cap_returns_clear_402_without_server_error(monkeypatch):
    deps._reset_trial_meter()
    monkeypatch.setattr(deps, "teacher", None)
    monkeypatch.setenv("ALLOW_SERVER_FALLBACK_KEY", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "server-side-fallback-key")
    monkeypatch.setenv("TRIAL_FREE_CALLS", "5")
    monkeypatch.setenv("TRIAL_GLOBAL_DAILY_CAP", "1")

    with patch("app.dependencies.OpenRouterTeacher") as mock_teacher_cls:
        mock_teacher = MagicMock()
        mock_teacher.chat.return_value = "Final funded answer"
        mock_teacher_cls.return_value = mock_teacher

        first = client.post("/api/chat", json=CHAT_PAYLOAD)
        blocked = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert first.status_code == 200
    assert first.headers["X-Trial-Remaining"] == "0"
    assert blocked.status_code == 402
    assert "unavailable for today" in blocked.json()["detail"]
