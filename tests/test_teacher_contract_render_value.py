"""Tests for teacher/contract.py — _coerce_text / _render_value scalar-to-markdown helpers."""

from teacher.contract import _coerce_text, _render_value


# --------------------------------------------------------------------------
# _coerce_text
# --------------------------------------------------------------------------


def test_coerce_text_passes_through_strings_unchanged():
    assert _coerce_text("hello") == "hello"


def test_coerce_text_none_becomes_empty_string():
    assert _coerce_text(None) == ""


def test_coerce_text_stringifies_int():
    assert _coerce_text(42) == "42"


def test_coerce_text_stringifies_float():
    assert _coerce_text(3.5) == "3.5"


def test_coerce_text_stringifies_bool():
    assert _coerce_text(True) == "True"
    assert _coerce_text(False) == "False"


# --------------------------------------------------------------------------
# _render_value
# --------------------------------------------------------------------------


def test_render_value_scalar_returns_plain_text():
    assert _render_value("plain") == "plain"


def test_render_value_none_returns_empty_string():
    assert _render_value(None) == ""


def test_render_value_dict_renders_bullet_list_with_capitalized_key():
    assert _render_value({"foo_bar": "baz"}) == "- **Foo bar**: baz"


def test_render_value_dict_capitalizes_and_lowercases_rest_of_shouty_key():
    assert _render_value({"MULTI_WORD_KEY": "x"}) == "- **Multi word key**: x"


def test_render_value_nested_dict_recurses_inline():
    assert (
        _render_value({"outer": {"inner": "value"}})
        == "- **Outer**: - **Inner**: value"
    )


def test_render_value_list_of_scalars_joins_with_comma():
    assert _render_value(["a", "b", "c"]) == "a, b, c"


def test_render_value_tuple_joins_with_comma():
    assert _render_value(("x", "y")) == "x, y"


def test_render_value_list_of_dicts_renders_each_item():
    assert _render_value([{"a": 1}]) == "- **A**: 1"


def test_render_value_empty_dict_returns_empty_string():
    assert _render_value({}) == ""


def test_render_value_empty_list_returns_empty_string():
    assert _render_value([]) == ""
