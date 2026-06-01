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


def _make_temp_js(content: str) -> str:
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    path = os.path.join(tmp_dir, "sample.js")
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

    def test_snippet_javascript_uses_metadata_range(self):
        path = _make_temp_js(
            "// prelude\nexport function greet(name) {\n  return `hi ${name}`;\n}\n"
        )
        resp = client.post(
            "/api/snippet",
            json={
                "file_path": path,
                "node_id": "greet",
                "language": "javascript",
                "start_line": 2,
                "end_line": 4,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "export function greet" in data["snippet"]
        assert data["start_line"] == 2
        assert data["end_line"] == 4
        assert data["language"] == "javascript"


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
            json={
                "file_path": "sample.py",
                "node_id": "hello",
                "level": "beginner",
                "callers": ["entry.main"],
                "callees": ["helper.clean"],
                "neighbors": ["entry.main", "helper.clean"],
                "language": "javascript",
                "start_line": 2,
                "end_line": 4,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["explanation"]["analogy"] == "A greeting card"
        assert data["explanation"]["technical"] == "Defines a no-op function"
        assert data["explanation"]["key_takeaway"] == "Simple function definition"
        _, kwargs = mock_teacher.explain_code.call_args
        assert kwargs["node_id"] == "hello"
        assert kwargs["file_path"] == "sample.py"
        assert kwargs["callers"] == ["entry.main"]
        assert kwargs["callees"] == ["helper.clean"]
        assert kwargs["neighbors"] == ["entry.main", "helper.clean"]
        mock_snippet.assert_called_once_with(
            "sample.py",
            "hello",
            language="javascript",
            start_line=2,
            end_line=4,
        )

    @patch("app.routers.explain.deps.get_teacher_for_request")
    def test_explain_javascript_sends_real_snippet_to_teacher(self, mock_get_teacher):
        path = _make_temp_js("export function greet() {\n  return 'hi';\n}\n")
        mock_teacher = MagicMock()
        mock_teacher.explain_code.return_value = {
            "analogy": "Greeting",
            "technical": "Returns a string",
            "key_takeaway": "JS source is available",
        }
        mock_get_teacher.return_value = mock_teacher

        resp = client.post(
            "/api/explain",
            json={
                "file_path": path,
                "node_id": "greet",
                "level": "beginner",
                "language": "javascript",
            },
        )

        assert resp.status_code == 200
        snippet = mock_teacher.explain_code.call_args.args[0]
        assert "export function greet" in snippet
        assert "Syntax error" not in snippet

    @patch("app.routers.explain.deps.get_teacher_for_request")
    def test_explain_without_api_key_returns_401(self, mock_get_teacher):
        mock_get_teacher.side_effect = HTTPException(
            status_code=401, detail="API key required"
        )
        test_file_path = _make_temp_py()
        resp = client.post(
            "/api/explain",
            json={"file_path": test_file_path, "node_id": "hello"},
        )
        assert resp.status_code == 401
