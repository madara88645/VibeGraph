"""Tests for app/routers/learning.py — /api/learning-path endpoint."""

import os
import tempfile

from unittest.mock import MagicMock, patch

import networkx as nx
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


class TestLearningPath:
    @patch("app.routers.learning.deps.get_teacher_for_request")
    @patch("app.routers.learning.CodeAnalyzer")
    def test_valid_request(self, mock_analyzer_cls, mock_get_teacher):
        path = _make_temp_py("def hello():\n    pass\n\ndef world():\n    hello()\n")

        graph = nx.DiGraph()
        graph.add_node("hello", type="function")
        graph.add_node("world", type="function")
        graph.add_edge("world", "hello")

        mock_analyzer = MagicMock()
        mock_analyzer.analyze_file.return_value = {"graph": graph}
        mock_analyzer_cls.return_value = mock_analyzer

        mock_teacher = MagicMock()
        mock_teacher.suggest_learning_path.return_value = [
            {"step": 1, "node_id": "hello", "reason": "No dependencies"},
            {"step": 2, "node_id": "world", "reason": "Calls hello"},
        ]
        mock_get_teacher.return_value = mock_teacher

        resp = client.post("/api/learning-path", json={"file_path": path})
        assert resp.status_code == 200
        data = resp.json()
        assert data["file_path"] == path
        assert len(data["steps"]) == 2
        assert data["steps"][0]["node_id"] == "hello"

    def test_nonexistent_file_returns_404(self):
        tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
        fake = os.path.join(tmp_dir, "nope.py")
        resp = client.post("/api/learning-path", json={"file_path": fake})
        assert resp.status_code == 404

    def test_unsafe_path_returns_403(self):
        resp = client.post(
            "/api/learning-path",
            json={"file_path": "../../etc/passwd"},
        )
        assert resp.status_code == 403

    @patch("app.routers.learning.CodeAnalyzer")
    def test_analysis_error_returns_400(self, mock_analyzer_cls):
        path = _make_temp_py()

        mock_analyzer = MagicMock()
        mock_analyzer.analyze_file.return_value = {"error": "Parse failed"}
        mock_analyzer_cls.return_value = mock_analyzer

        resp = client.post("/api/learning-path", json={"file_path": path})
        assert resp.status_code == 400
        assert "Parse failed" in resp.json()["detail"]
