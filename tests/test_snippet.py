"""Tests for app/utils/snippet.py — AST-based code snippet extraction."""

import os
from unittest import mock
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


def _write_temp_path(relative_path: str, content: str) -> str:
    """Write *content* under a vibegraph_test_ directory using relative_path."""
    tmp_dir = tempfile.mkdtemp(prefix="vibegraph_test_")
    path = os.path.join(tmp_dir, *relative_path.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
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
            "class Greeter:\n    def greet(self):\n        return 'hi'\n"
        )
        code, start, end, full_source = extract_snippet(path, "Greeter")
        assert "class Greeter:" in code
        assert start == 1

    def test_extract_dotted_node_id(self):
        """node_id like 'Greeter.greet' should resolve to 'greet'."""
        path = _write_temp(
            "class Greeter:\n    def greet(self):\n        return 'hi'\n"
        )
        code, start, end, _ = extract_snippet(path, "Greeter.greet")
        assert "def greet(self):" in code

    def test_extract_javascript_with_line_metadata(self):
        path = _write_temp_path(
            "src/sample.js",
            "// setup\nexport function greet(name) {\n  return `hi ${name}`;\n}\n",
        )
        code, start, end, full_source = extract_snippet(
            path,
            "greet",
            language="javascript",
            start_line=2,
            end_line=4,
        )
        assert "export function greet" in code
        assert "return `hi ${name}`" in code
        assert start == 2
        assert end == 4
        assert full_source is not None

    def test_extract_typescript_with_line_metadata(self):
        path = _write_temp_path(
            "src/widget.tsx",
            "import React from 'react';\nexport function Widget() {\n  return <section />;\n}\n",
        )
        code, start, end, full_source = extract_snippet(
            path,
            "Widget",
            language="typescript",
            start_line=2,
            end_line=4,
        )
        assert "export function Widget" in code
        assert "return <section />" in code
        assert start == 2
        assert end == 4
        assert full_source is not None

    def test_extract_javascript_without_metadata_uses_analyzer_fallback(self):
        path = _write_temp_path(
            "src/sample.js",
            "export function greet(name) {\n  return `hi ${name}`;\n}\n",
        )
        code, start, end, full_source = extract_snippet(
            path,
            "greet",
            language="javascript",
        )
        assert "export function greet" in code
        assert start == 1
        assert end == 3
        assert full_source is not None

    def test_module_node_returns_full_source(self):
        source = "export function greet() {\n  return 'hi';\n}\n"
        path = _write_temp_path("src/sample.js", source)
        code, start, end, full_source = extract_snippet(
            path,
            "module:sample",
            language="javascript",
        )
        assert code == source
        assert start == 1
        assert end == 3
        assert full_source == source


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
        assert "Source unavailable" in code
        assert "re-upload" in code
        assert start is None


class TestFileReadError:
    def test_oserror_on_read_returns_error(self):
        from unittest.mock import patch

        path = _write_temp("def hello():\n    pass\n")

        with patch("builtins.open", side_effect=OSError("Mocked OSError")):
            code, start, end, full_source = extract_snippet(path, "hello")

        assert "# Error reading file" in code
        assert start is None
        assert end is None
        assert full_source is None


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


class TestOSError:
    def test_oserror_returns_read_error(self):
        path = _write_temp("def hello():\n    pass\n")
        with mock.patch("builtins.open", side_effect=OSError("Mocked OSError")):
            code, start, end, full_source = extract_snippet(path, "hello")
        assert "Error reading file" in code
        assert start is None
        assert end is None
        assert full_source is None
