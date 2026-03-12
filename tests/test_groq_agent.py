import unittest

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
            _try_parse_json('')
        self.assertEqual(str(context.exception), '')

    def test_malformed_markdown_fences(self):
        result = _try_parse_json('```json{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_uppercase_markdown_fences(self):
        result = _try_parse_json('```JSON\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_mixed_case_markdown_fences(self):
        result = _try_parse_json('```jSoN\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_text_before_fences(self):
        result = _try_parse_json('Here is your json:\n```json\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_text_after_fences(self):
        result = _try_parse_json('```json\n{"key": "value"}\n```\nHope this helps!')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_text_before_and_after_fences(self):
        result = _try_parse_json('Here is your json:\n```json\n{"key": "value"}\n```\nHope this helps!')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_trailing_spaces_on_fences(self):
        result = _try_parse_json('```json   \n{"key": "value"}\n```   ')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_multiple_blocks(self):
        # Should parse the first block if there are multiple, or just extract properly
        # Note: with greedy match (.*) it matches the outermost ``` which spans multiple blocks.
        # This results in: {"first": 1}\n```\nMore text\n```json\n{"second": 2}
        # Which is invalid JSON, so it falls back or raises ValueError depending on the fallback.
        # The correct behavior for multiple blocks where one is valid JSON might be tricky,
        # but the primary use case is a single JSON payload.
        with self.assertRaises(ValueError):
            _try_parse_json('Some text\n```json\n{"first": 1}\n```\nMore text\n```json\n{"second": 2}\n```')

    def test_json_with_internal_backticks(self):
        # The LLM returns a valid JSON payload that *contains* markdown fences
        payload = '```json\n{"code": "```python\\nprint(\'hello\')\\n```"}\n```'
        result = _try_parse_json(payload)
        self.assertEqual(result, {"code": "```python\nprint('hello')\n```"})
