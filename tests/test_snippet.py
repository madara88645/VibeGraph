"""Tests for app/utils/snippet.py — AST-based code snippet extraction."""

import os
import tempfile

import pytest
from fastapi import HTTPException

from app.utils.snippet import extract_snippet, _get_parsed_ast
from analyst.analyzer import MAX_FILE_SIZE


@pytest.fixture(autouse=True)
def clear_ast_cache():
    """Clear the LRU cache before every test to ensure isolation."""
    _get_parsed_ast.cache_clear()
    yield
    _get_parsed_ast.cache_clear()


def _write_temp(content: str, suffix: str = ".py") -> str:
    """Write *content* to a temp file inside a vibegraph_test_ directory and return its path."""
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    path = os.path.join(tmp_dir, f"sample{suffix}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


class TestExtractFunction:
    def test_extract_function_from_valid_file(self):
        path = _write_temp("def hello():\n    pass\n")
        code, start, end, full_source = extract_snippet(path, "hello")
        assert "def hello():" in code
        assert start == 1
        assert end is not None
        assert full_source is not None

    def test_extract_class_from_valid_file(self):
        path = _write_temp(
            "class Greeter:\n"
            "    def greet(self):\n"
            "        return 'hi'\n"
        )
        code, start, end, full_source = extract_snippet(path, "Greeter")
        assert "class Greeter:" in code
        assert start == 1

    def test_extract_dotted_node_id(self):
        """node_id like 'Greeter.greet' should resolve to 'greet'."""
        path = _write_temp(
            "class Greeter:\n"
            "    def greet(self):\n"
            "        return 'hi'\n"
        )
        code, start, end, _ = extract_snippet(path, "Greeter.greet")
        assert "def greet(self):" in code


class TestNodeNotFound:
    def test_node_not_found_returns_fallback(self):
        path = _write_temp("def hello():\n    pass\n")
        code, start, end, full_source = extract_snippet(path, "nonexistent")
        assert "not found" in code.lower()
        assert start is None
        assert end is None
        assert full_source is not None


class TestExternalBuiltin:
    def test_both_none(self):
        code, start, end, full_source = extract_snippet(None, None)
        assert "External or Built-in" in code
        assert start is None
        assert full_source is None

    def test_file_path_none(self):
        code, _, _, _ = extract_snippet(None, "some_func")
        assert "External or Built-in" in code

    def test_node_id_none(self):
        code, _, _, _ = extract_snippet("/some/path.py", None)
        assert "External or Built-in" in code

    def test_nonexistent_file(self):
        tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
        fake = os.path.join(tmp_dir, "does_not_exist.py")
        code, start, end, full_source = extract_snippet(fake, "func")
        assert "External/Built-in" in code
        assert start is None


class TestSyntaxError:
    def test_syntax_error_returns_error_with_line_info(self):
        path = _write_temp("def broken(\n")
        code, start, end, full_source = extract_snippet(path, "broken")
        assert "Syntax error" in code
        assert "line" in code.lower()
        # full_source should still contain the raw file text
        assert full_source is not None


class TestOversizedFile:
    def test_oversized_file_returns_max_size_error(self):
        # Create a file just over MAX_FILE_SIZE
        tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
        path = os.path.join(tmp_dir, "big.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write("x = 1\n" * (MAX_FILE_SIZE // 5))
        code, start, end, full_source = extract_snippet(path, "x")
        assert "maximum allowed size" in code
        assert start is None


class TestUnsafePath:
    def test_dotdot_raises_403(self):
        with pytest.raises(HTTPException) as exc_info:
            extract_snippet("../../etc/passwd", "func")
        assert exc_info.value.status_code == 403
