"""Tests for teacher/openrouter_teacher.py — OpenRouterTeacher and helpers."""

import json

import pytest
from unittest.mock import MagicMock, patch

from openai import APITimeoutError
from app.dependencies import DEFAULT_OPENROUTER_MODEL
from teacher.openrouter_teacher import (
    OpenRouterTeacher,
    _try_parse_json,
    NarrateStepContext,
)


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

    def test_recovers_object_truncated_mid_value(self):
        # Model hit its token limit mid-string; we should still recover fields.
        truncated = '{"analogy": "a", "sections": {"What it is": "partial value cut o'
        result = _try_parse_json(truncated)
        assert result["analogy"] == "a"
        assert "partial value cut o" in result["sections"]["What it is"]

    def test_unrecoverable_garbage_still_raises(self):
        with pytest.raises(ValueError):
            _try_parse_json("totally not json {[}")


# ---------------------------------------------------------------------------
# OpenRouterTeacher construction
# ---------------------------------------------------------------------------
class TestTeacherConstruction:
    @patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}, clear=False)
    def test_no_api_key_sets_client_none(self):
        teacher = OpenRouterTeacher(api_key=None)
        assert teacher.client is None

    @patch.dict("os.environ", {}, clear=True)
    def test_default_model_matches_api_config_default(self):
        teacher = OpenRouterTeacher(api_key="sk-test-key")
        assert teacher.model_name == DEFAULT_OPENROUTER_MODEL


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
        assert (
            "unavailable" in result["narration"].lower()
            or "missing" in result["narration"].lower()
        )

    def test_suggest_learning_path_returns_missing_key(self):
        result = self.teacher.suggest_learning_path(
            nodes_summary="foo (function)",
            edges_summary="",
            file_path="test.py",
        )
        assert len(result) >= 1
        assert (
            "missing" in result[0]["reason"].lower()
            or "key" in result[0]["node_id"].lower()
        )


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
        response_json = json.dumps(
            {
                "analogy": "Like a recipe",
                "key_takeaway": "Functions encapsulate logic",
                "sections": {
                    "What it is": "Defines a function",
                    "Inputs/Outputs": "No input and no output",
                    "Side effects": "No side effects",
                    "Why this node exists": "Serves as simple behavior",
                    "Common bugs": "None here",
                    "References": "Selected node: foo",
                    "Unknowns": "Unknown (not in provided code context).",
                },
                "unknowns": ["Unknown (not in provided code context)."],
            }
        )
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        result = self.teacher.explain_code(
            "def foo(): pass", node_id="foo", file_path="demo.py"
        )
        assert result["analogy"] == "Like a recipe"
        assert "### What it is" in result["technical"]
        assert "### References" in result["technical"]
        assert "Selected node: foo" in result["technical"]
        assert result["key_takeaway"] == "Functions encapsulate logic"

    def test_explain_code_external_node_dict_technical(self):
        """Issue #405: external/built-in node payloads carry a dict `technical`
        and list-valued sections. The result must be a valid string-typed
        ExplanationDetail that preserves the structured details."""
        from app.models import ExplanationDetail

        response_json = json.dumps(
            {
                "analogy": "handle_export is like a gatekeeper that bridges results.",
                "technical": {
                    "origin": "External (likely defined in dependency package 'analyst')",
                    "signature": "Callable[[...], Any] (exact signature unknown)",
                    "callers": ["main", "module:main"],
                    "callees": ["external:rich.panel.Panel", "unresolved:print"],
                },
                "key_takeaway": "Orchestrates exporting analysis results to React Flow.",
                "sections": {
                    "What it is": "A function that coordinates exporting analysis data.",
                    "Inputs/Outputs": "Inputs: Unknown. Outputs: Unknown.",
                    "Side effects": "Likely prints to stdout and displays a Panel.",
                    "Why this node exists": "To decouple analysis from export.",
                    "Common bugs": [
                        "Unresolved callees may cause runtime ImportError",
                        "No explicit error handling could lead to unhandled exceptions",
                    ],
                    "References": [
                        "Callers: main, module:main",
                        "Neighbors: print, Panel, CodeAnalyzer",
                    ],
                },
                "unknowns": ["Exact signature of handle_export."],
            }
        )
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        result = self.teacher.explain_code(
            "", context="External Library / Built-in", node_id="handle_export"
        )

        # The technical field must always be a string (Pydantic contract).
        assert isinstance(result["technical"], str)
        # Structured technical metadata is preserved, not dropped.
        assert "Technical Details" in result["technical"]
        assert (
            "External (likely defined in dependency package 'analyst')"
            in (result["technical"])
        )
        # List-valued sections render readably, not as Python list repr.
        assert "['" not in result["technical"]
        assert "Unresolved callees may cause runtime ImportError" in result["technical"]
        # The Pydantic model accepts the result without raising.
        detail = ExplanationDetail(**result)
        assert isinstance(detail.technical, str)

    def test_explain_code_recovers_from_truncated_json(self):
        """A response truncated at the token limit must degrade to usable
        content instead of surfacing an 'AI Formatting Error'."""
        truncated = (
            '{"analogy": "like a conductor", '
            '"key_takeaway": "entry point", '
            '"sections": {"What it is": "Coordinates the analysis pipeline'
        )
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            truncated
        )
        result = self.teacher.explain_code(
            "def handle_start(): pass", node_id="handle_start", file_path="main.py"
        )
        assert not result.get("is_error")
        assert result["analogy"] == "like a conductor"
        assert "Coordinates the analysis pipeline" in result["technical"]

    def test_explain_code_caches_results(self):
        response_json = json.dumps(
            {
                "analogy": "cached",
                "technical": "cached",
                "key_takeaway": "cached",
            }
        )
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
        response_json = json.dumps(
            {
                "narration": "This function initializes the app",
                "relationship": "calls",
                "importance": "high",
            }
        )
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

    def test_narrate_step_repairs_invalid_importance(self):
        response_json = json.dumps(
            {
                "narration": "This function initializes the app",
                "relationship": "calls helper",
                "importance": "critical",
            }
        )
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        ctx = NarrateStepContext(code_snippet="def init(): pass", node_id="init")
        result = self.teacher.narrate_step(ctx)
        assert result["importance"] == "medium"

    def test_narrate_step_handles_api_timeout_error(self):
        request = MagicMock()
        self.mock_client.chat.completions.create.side_effect = APITimeoutError(request)
        ctx = NarrateStepContext(code_snippet="def init(): pass", node_id="init")
        result = self.teacher.narrate_step(ctx)
        assert result["narration"] == "Narration timed out."
        assert result["relationship"] == ""
        assert result["importance"] == "low"

    def test_narrate_step_handles_generic_exception(self):
        self.mock_client.chat.completions.create.side_effect = Exception(
            "Unexpected error"
        )
        ctx = NarrateStepContext(code_snippet="def init(): pass", node_id="init")
        result = self.teacher.narrate_step(ctx)
        assert result["narration"] == ""
        assert result["relationship"] == ""
        assert result["importance"] == "low"

    def test_refine_learning_path_prompt_constrains_allowed_nodes(self):
        response_json = json.dumps(
            {
                "steps": [
                    {"node_id": "helper", "reason": "Read helper second"},
                    {"node_id": "main", "reason": "Entry point"},
                ]
            }
        )
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )

        result = self.teacher.refine_learning_path(
            [
                {"node_id": "main", "reason": "Entry point"},
                {"node_id": "helper", "reason": "Called by main"},
            ],
            allowed_node_ids=["main", "helper"],
        )

        assert [step["node_id"] for step in result] == ["helper", "main"]
        kwargs = self.mock_client.chat.completions.create.call_args.kwargs
        prompt = kwargs["messages"][1]["content"]
        assert "Do not add/remove node_ids" in prompt
        assert "allowed_node_ids" in prompt
        assert "main" in prompt
        assert "helper" in prompt

    def test_refine_learning_path_strips_heavy_fields_from_prompt(self):
        """Prompt must not include score/signals/step — only the fields the
        model needs to reorder. Saves prompt input tokens."""
        response_json = json.dumps({"steps": []})
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )

        self.teacher.refine_learning_path(
            [
                {
                    "node_id": "main",
                    "node_name": "main",
                    "file_path": "repo/main.py",
                    "reason": "Entry point",
                    "score": 173.42,
                    "signals": {"hub_score": 25.0, "fan_in": 3, "fan_out": 7},
                    "step": 1,
                },
            ],
            allowed_node_ids=["main"],
        )

        prompt = self.mock_client.chat.completions.create.call_args.kwargs["messages"][
            1
        ]["content"]
        # Allowlist contents must still be present.
        assert "main" in prompt
        assert "repo/main.py" in prompt
        # Heavy fields must be stripped from the baseline_steps payload.
        assert "173.42" not in prompt
        assert "hub_score" not in prompt
        assert '"step":' not in prompt and '"step": ' not in prompt

    def test_refine_learning_path_malformed_response_returns_empty_refinement(self):
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            '{"unexpected": []}'
        )

        result = self.teacher.refine_learning_path(
            [{"node_id": "main", "reason": "Entry point"}],
            allowed_node_ids=["main"],
        )

        assert result == []

    def test_chat_normalizes_sections_and_unknowns(self):
        response_json = json.dumps(
            {
                "sections": {
                    "What it is": "This node validates payloads.",
                    "Inputs/Outputs": "Input request -> validated object",
                    "Side effects": "No external side effects",
                    "Why this node exists": "Central validation logic",
                    "Common bugs": "Missing required keys",
                    "References": "Selected node: validate_request",
                    "Unknowns": "",
                },
                "unknowns": [],
            }
        )
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        answer = self.teacher.chat(
            code_snippet="def validate_request(req): return req",
            question="what does this do?",
            node_id="validate_request",
            file_path="api.py",
        )
        expected_order = [
            "### What it is",
            "### Inputs/Outputs",
            "### Side effects",
            "### Why this node exists",
            "### Common bugs",
            "### References",
            "### Unknowns",
        ]
        positions = [answer.index(section) for section in expected_order]
        assert positions == sorted(positions)
        assert "Selected node: validate_request" in answer

    def test_suggest_learning_path_filters_unknown_node_ids(self):
        response_json = json.dumps(
            {
                "steps": [
                    {"step": 1, "node_id": "fake", "reason": "invented"},
                    {"step": 2, "node_id": "main", "reason": "entry point"},
                ]
            }
        )
        self.mock_client.chat.completions.create.return_value = _mock_completion(
            response_json
        )
        result = self.teacher.suggest_learning_path(
            nodes_summary="main (function), helper (function)",
            edges_summary="main → helper",
            file_path="sample.py",
            allowed_node_ids=["main", "helper"],
        )
        assert [step["node_id"] for step in result] == ["main"]
