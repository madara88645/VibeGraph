"""Tests for app/routers/explain.py — /api/snippet and /api/explain endpoints."""

import os
import tempfile

from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import create_app

app = create_app()
client = TestClient(app, raise_server_exceptions=False)


def _make_temp_py(content: str = "def hello():\n    pass\n") -> str:
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    path = os.path.join(tmp_dir, "sample.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestSnippetEndpoint:
    def test_snippet_valid_file(self):
        path = _make_temp_py()
        resp = client.post(
            "/api/snippet",
            json={"file_path": path, "node_id": "hello"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "def hello():" in data["snippet"]
        assert data["node_id"] == "hello"
        assert data["start_line"] is not None

    def test_snippet_none_file_path(self):
        resp = client.post(
            "/api/snippet",
            json={"file_path": None, "node_id": "os.path.join"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "External or Built-in" in data["snippet"]


class TestExplainEndpoint:
    @patch("app.routers.explain.deps.get_teacher_for_request")
    @patch("app.routers.explain.extract_snippet")
    def test_explain_with_mocked_teacher(self, mock_snippet, mock_get_teacher):
        mock_snippet.return_value = ("def hello(): pass", 1, 1, None)

        mock_teacher = MagicMock()
        mock_teacher.explain_code.return_value = {
            "analogy": "A greeting card",
            "technical": "Defines a no-op function",
            "key_takeaway": "Simple function definition",
        }
        mock_get_teacher.return_value = mock_teacher

        resp = client.post(
            "/api/explain",
            json={"file_path": "sample.py", "node_id": "hello", "level": "beginner"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["explanation"]["analogy"] == "A greeting card"
        assert data["explanation"]["technical"] == "Defines a no-op function"
        assert data["explanation"]["key_takeaway"] == "Simple function definition"

    @patch("app.routers.explain.deps.get_teacher_for_request")
    def test_explain_without_api_key_returns_401(self, mock_get_teacher):
        mock_get_teacher.side_effect = HTTPException(
            status_code=401, detail="API key required"
        )
        resp = client.post(
            "/api/explain",
            json={"file_path": "sample.py", "node_id": "hello"},
        )
        assert resp.status_code == 401
