"""Direct unit tests for teacher/openrouter_teacher.py's
`_repair_truncated_json` helper.

`tests/test_openrouter_teacher.py` exercises this function only indirectly
through `_try_parse_json`, and only for two shapes: a string truncated
mid-value, and unparseable garbage. This file targets the bracket/quote-stack
repair logic directly, including branches the indirect coverage misses:
escaped quotes inside a truncated string, dangling trailing colon/comma
stripping, multi-level (array + object) stack closing, and a truncation that
is unrecoverable because it ends on a dangling key with no value.
"""

from app.dependencies import DEFAULT_OPENROUTER_MODEL  # noqa: F401  (see module docstring below)
from teacher.openrouter_teacher import _repair_truncated_json


# NOTE: `app.dependencies` must be imported before `teacher.openrouter_teacher`
# here to avoid a circular-import error (app/__init__.py -> app.routers.ai ->
# app.dependencies -> teacher.openrouter_teacher). The sibling test file
# `tests/test_openrouter_teacher.py` uses the same import ordering.


class TestRepairTruncatedJson:
    def test_no_opening_brace_returns_none(self):
        assert _repair_truncated_json("no braces here at all") is None

    def test_closes_string_truncated_mid_value(self):
        result = _repair_truncated_json('{"a": "hello')
        assert result == {"a": "hello"}

    def test_escaped_quote_inside_truncated_string_does_not_close_early(self):
        # The backslash-escaped quote must not be treated as the string
        # terminator; the repair should still recognize we're inside an
        # open string and close it (not close the object early / corrupt
        # the value).
        text = r'{"a": "value with \"escaped\" quote and more untermin'
        result = _repair_truncated_json(text)
        assert result == {"a": 'value with "escaped" quote and more untermin'}

    def test_strips_dangling_trailing_comma_before_closing(self):
        result = _repair_truncated_json('{"a": 1, "b": 2,')
        assert result == {"a": 1, "b": 2}

    def test_dangling_trailing_colon_with_no_value_is_unrecoverable(self):
        # Stripping the dangling colon leaves a bare key with no value,
        # which is still invalid JSON -- repair must fail closed (None),
        # not fabricate a value.
        result = _repair_truncated_json('{"a": "done", "b":')
        assert result is None

    def test_closes_truncated_array_value(self):
        result = _repair_truncated_json('{"items": [1, 2, 3')
        assert result == {"items": [1, 2, 3]}

    def test_closes_multiple_nesting_levels_object_in_array_in_object(self):
        result = _repair_truncated_json('{"a": [{"b": 1, "c": 2')
        assert result == {"a": [{"b": 1, "c": 2}]}

    def test_already_complete_object_round_trips(self):
        assert _repair_truncated_json('{"a": 1}') == {"a": 1}
        assert _repair_truncated_json("{}") == {}

    def test_ignores_leading_prose_before_first_brace(self):
        # A model sometimes prefixes JSON with commentary; the repair looks
        # for the first '{' and works from there.
        result = _repair_truncated_json('Sure, here is the JSON: {"a": 1')
        assert result == {"a": 1}

    def test_stray_unmatched_closing_bracket_does_not_raise_and_fails_closed(self):
        # A close bracket with no corresponding opener on the stack is a
        # no-op against the (empty) stack rather than raising, but the
        # resulting text ("extra data" after an already-complete object) is
        # still not valid JSON -- repair must fail closed (None), not crash.
        result = _repair_truncated_json('{"a": 1}}')
        assert result is None
