import unittest
import json

from teacher.groq_agent import _try_parse_json


class TestTryParseJson(unittest.TestCase):
    def test_valid_json(self):
        result = _try_parse_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_markdown_fences(self):
        result = _try_parse_json('```\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_json_markdown_fences(self):
        result = _try_parse_json('```json\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_whitespace(self):
        result = _try_parse_json('   \n  {"key": "value"} \n  ')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_markdown_fences_and_whitespace(self):
        result = _try_parse_json('   \n  ```json\n{"key": "value"}\n``` \n  ')
        self.assertEqual(result, {"key": "value"})

    def test_invalid_json(self):
        with self.assertRaises(ValueError) as context:
            _try_parse_json('{"key": "value"')
        self.assertEqual(str(context.exception), '{"key": "value"')

    def test_empty_string(self):
        with self.assertRaises(ValueError) as context:
            _try_parse_json("")
        self.assertEqual(str(context.exception), "")

    def test_malformed_markdown_fences(self):
        result = _try_parse_json('```json{"key": "value"}')
        self.assertEqual(result, {"key": "value"})


from unittest.mock import patch, MagicMock
from teacher.groq_agent import GroqTeacher


def test_explain_code_exception_leak():
    """Ensure explain_code does not leak exception details on error."""
    with patch("teacher.groq_agent.Groq") as MockGroq:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("SECRET_API_ERROR")
        MockGroq.return_value = mock_client

        teacher = GroqTeacher()
        # Force client to exist
        teacher.client = mock_client

        result = teacher.explain_code("def foo(): pass")

        assert "SECRET_API_ERROR" not in result.get("technical", "")
        assert result.get("technical") == "An unexpected error occurred."


def test_chat_exception_leak():
    """Ensure chat does not leak exception details on error."""
    with patch("teacher.groq_agent.Groq") as MockGroq:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("SECRET_API_ERROR")
        MockGroq.return_value = mock_client

        teacher = GroqTeacher()
        teacher.client = mock_client

        result = teacher.chat("def foo(): pass", "hello")

        assert "SECRET_API_ERROR" not in result
        assert result == "⚠️ Groq API error: An unexpected error occurred."


def test_suggest_learning_path_exception_leak():
    """Ensure suggest_learning_path does not leak exception details on error."""
    with patch("teacher.groq_agent.Groq") as MockGroq:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("SECRET_API_ERROR")
        MockGroq.return_value = mock_client

        teacher = GroqTeacher()
        teacher.client = mock_client

        result = teacher.suggest_learning_path("nodes", "edges", "test.py")

        assert len(result) == 1
        assert "SECRET_API_ERROR" not in result[0].get("reason", "")
        assert result[0].get("reason") == "An unexpected error occurred."


def test_explain_code_cache_uses_lru_recency():
    with patch("teacher.groq_agent._MAX_CACHE_SIZE", 2):
        teacher = GroqTeacher()
        teacher.client = MagicMock()

        def fake_create(*args, **kwargs):
            code = (
                kwargs["messages"][1]["content"]
                .split("```python\n", 1)[1]
                .split("\n```", 1)[0]
            )
            payload = {
                "analogy": f"analogy:{code}",
                "technical": f"technical:{code}",
                "key_takeaway": f"takeaway:{code}",
            }
            return MagicMock(
                choices=[MagicMock(message=MagicMock(content=json.dumps(payload)))]
            )

        teacher.client.chat.completions.create.side_effect = fake_create

        teacher.explain_code("print('a')")
        teacher.explain_code("print('b')")
        teacher.explain_code("print('a')")
        teacher.explain_code("print('c')")
        teacher.explain_code("print('a')")
        teacher.explain_code("print('b')")

        assert teacher.client.chat.completions.create.call_count == 4
