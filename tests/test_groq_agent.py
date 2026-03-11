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
