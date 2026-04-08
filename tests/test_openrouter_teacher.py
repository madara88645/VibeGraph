"""Tests for teacher/openrouter_teacher.py — OpenRouterTeacher and helpers."""

import json

import pytest
from unittest.mock import MagicMock, patch

from teacher.openrouter_teacher import OpenRouterTeacher, _try_parse_json, NarrateStepContext


def _mock_completion(content: str) -> MagicMock:
    """Build a mock OpenAI-style chat completion."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = content
    return mock


# ---------------------------------------------------------------------------
# _try_parse_json
# ---------------------------------------------------------------------------
class TestTryParseJson:
    def test_valid_json(self):
        result = _try_parse_json('{"a": 1, "b": "two"}')
        assert result == {"a": 1, "b": "two"}

    def test_strips_markdown_fences(self):
        wrapped = '```json\n{"key": "value"}\n```'
        result = _try_parse_json(wrapped)
        assert result == {"key": "value"}

    def test_strips_plain_fences(self):
        wrapped = '```\n{"key": "value"}\n```'
        result = _try_parse_json(wrapped)
        assert result == {"key": "value"}

    def test_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError):
            _try_parse_json("not json at all")


# ---------------------------------------------------------------------------
# OpenRouterTeacher construction
# ---------------------------------------------------------------------------
class TestTeacherConstruction:
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}, clear=False)
    def test_no_api_key_sets_client_none(self):
        teacher = OpenRouterTeacher(api_key=None)
        assert teacher.client is None


# ---------------------------------------------------------------------------
# Methods without a client (no API key)
# ---------------------------------------------------------------------------
class TestWithoutClient:
    def setup_method(self):
        self.teacher = OpenRouterTeacher.__new__(OpenRouterTeacher)
        self.teacher.client = None
        self.teacher.api_key = None
        self.teacher.model_name = "anthropic/claude-haiku-4.5"
        self.teacher._explain_cache = {}
        self.teacher._cache_lock = __import__("threading").RLock()

    def test_explain_code_returns_fallback(self):
        result = self.teacher.explain_code("def foo(): pass")
        assert result["analogy"] == "API Key Missing"
        assert "key" in result["key_takeaway"].lower()

    def test_chat_returns_key_missing(self):
        result = self.teacher.chat("code", "what does this do?")
        assert "key missing" in result.lower() or "api key" in result.lower()

    def test_stream_chat_yields_key_missing(self):
        chunks = list(self.teacher.stream_chat("code", "question"))
        combined = "".join(chunks)
        assert "key missing" in combined.lower() or "api key" in combined.lower()

    def test_narrate_step_returns_unavailable(self):
        ctx = NarrateStepContext(code_snippet="pass", node_id="foo")
        result = self.teacher.narrate_step(ctx)
        assert "unavailable" in result["narration"].lower() or "missing" in result["narration"].lower()

    def test_suggest_learning_path_returns_missing_key(self):
        result = self.teacher.suggest_learning_path(
            nodes_summary="foo (function)",
            edges_summary="",
            file_path="test.py",
        )
        assert len(result) >= 1
        assert "missing" in result[0]["reason"].lower() or "key" in result[0]["node_id"].lower()


# ---------------------------------------------------------------------------
# Methods with a mocked client
# ---------------------------------------------------------------------------
class TestWithMockedClient:
    @patch("teacher.openrouter_teacher.OpenAI")
    def setup_method(self, method, mock_openai_cls=None):
        self.mock_client = MagicMock()
        if mock_openai_cls is not None:
            mock_openai_cls.return_value = self.mock_client
        self.teacher = OpenRouterTeacher(api_key="sk-test-key")
        self.teacher.client = self.mock_client
        # Clear internal caches between tests
        self.teacher._explain_cache.clear()

    def test_explain_code_returns_parsed(self):
        response_json = json.dumps({
            "analogy": "Like a recipe",
            "technical": "Defines a function",
            "key_takeaway": "Functions encapsulate logic",
        })
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        result = self.teacher.explain_code("def foo(): pass")
        assert result["analogy"] == "Like a recipe"
        assert result["technical"] == "Defines a function"
        assert result["key_takeaway"] == "Functions encapsulate logic"

    def test_explain_code_caches_results(self):
        response_json = json.dumps({
            "analogy": "cached",
            "technical": "cached",
            "key_takeaway": "cached",
        })
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        # First call hits the API
        result1 = self.teacher.explain_code("def bar(): pass")
        # Second identical call should hit the cache
        result2 = self.teacher.explain_code("def bar(): pass")
        assert result1 == result2
        # Only one API call should have been made
        assert self.mock_client.chat.completions.create.call_count == 1

    def test_narrate_step_returns_narration_dict(self):
        response_json = json.dumps({
            "narration": "This function initializes the app",
            "relationship": "calls",
            "importance": "high",
        })
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        ctx = NarrateStepContext(
            code_snippet="def init(): setup()",
            node_id="init",
            previous_node_id="main",
        )
        result = self.teacher.narrate_step(ctx)
        assert result["narration"] == "This function initializes the app"
        assert result["relationship"] == "calls"
        assert result["importance"] == "high"
