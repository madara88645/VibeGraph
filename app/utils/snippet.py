"""Source code snippet extraction for supported VibeGraph languages."""

import ast
import collections
import functools
import logging
import os
from typing import Any

from fastapi import HTTPException

from analyst.analyzer import MAX_FILE_SIZE
from app.utils.security import is_safe_path

logger = logging.getLogger(__name__)


JS_LANGUAGES = frozenset({"javascript", "typescript"})
JS_EXTENSIONS = frozenset({".js", ".jsx", ".mjs", ".cjs"})
TS_EXTENSIONS = frozenset({".ts", ".tsx"})


def _normalize_language(language: str | None, file_path: str | None) -> str | None:
    if isinstance(language, str):
        cleaned = language.strip().lower()
        if cleaned in {"js", "jsx", "javascript"}:
            return "javascript"
        if cleaned in {"ts", "tsx", "typescript"}:
            return "typescript"
        if cleaned in {"py", "python"}:
            return "python"

    ext = os.path.splitext(file_path or "")[1].lower()
    if ext in JS_EXTENSIONS:
        return "javascript"
    if ext in TS_EXTENSIONS:
        return "typescript"
    if ext == ".py":
        return "python"
    return None


@functools.lru_cache(maxsize=128)
def _get_source_text(
    resolved_path: str, mtime: float
) -> tuple[str | None, list[str] | None, str | None]:
    try:
        if os.path.getsize(resolved_path) > MAX_FILE_SIZE:
            return (
                None,
                None,
                f"# Error: File exceeds maximum allowed size ({MAX_FILE_SIZE} bytes).",
            )
        with open(resolved_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError:
        logger.warning("Snippet read failed for %s", resolved_path, exc_info=True)
        return None, None, "# Error reading file. It may be missing or inaccessible."

    return source, source.splitlines(), None


@functools.lru_cache(maxsize=128)
def _get_parsed_ast(
    resolved_path: str, mtime: float
) -> tuple[
    str | None,
    ast.AST | None,
    list[str] | None,
    dict[str, tuple[int, int | None]] | None,
    str | None,
]:
    source, lines, read_error = _get_source_text(resolved_path, mtime)
    if read_error:
        return source, None, lines, None, read_error
    assert source is not None
    assert lines is not None

    try:
        tree = ast.parse(source, filename=resolved_path)
    except SyntaxError as e:
        logger.info(
            "Snippet parse failed for %s at line=%s column=%s",
            resolved_path,
            e.lineno,
            e.offset,
        )
        location_parts = []
        if e.lineno is not None:
            location_parts.append(f"line {e.lineno}")
        if e.offset is not None:
            location_parts.append(f"column {e.offset}")
        location = f" ({', '.join(location_parts)})" if location_parts else ""
        return source, None, None, None, f"# Syntax error in file{location}."

    lines = source.splitlines()
    nodes = {}

    # PERFORMANCE OPTIMIZATION (Bolt): Replaced ast.walk (which visits all leaves)
    # with a targeted BFS using deque to massively speed up parsing large ASTs,
    # while preserving BFS-first-name-wins shadowing behavior.
    queue: collections.deque[ast.AST] = collections.deque([tree])
    while queue:
        current = queue.popleft()

        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if current.name not in nodes:
                nodes[current.name] = (current.lineno, current.end_lineno)

        # Only recurse into structural blocks where new definitions can exist
        for attr in ("body", "orelse", "handlers", "finalbody", "cases"):
            child_list = getattr(current, attr, None)
            if isinstance(child_list, list):
                for child in child_list:
                    if isinstance(child, ast.AST):
                        queue.append(child)

    return source, tree, lines, nodes, None


def _slice_lines(
    source: str,
    lines: list[str],
    start_line: int | None,
    end_line: int | None,
) -> tuple[str | None, int | None, int | None]:
    if start_line is None or end_line is None:
        return None, None, None
    if start_line < 1 or end_line < start_line or start_line > len(lines):
        return None, None, None

    safe_end = min(end_line, len(lines))
    snippet = "\n".join(lines[start_line - 1 : safe_end])
    if source.endswith("\n") and safe_end == len(lines):
        snippet += "\n"
    return snippet, start_line, safe_end


def _module_snippet(source: str, lines: list[str]) -> tuple[str, int, int]:
    return source, 1, max(len(lines), 1)


def _find_graph_node_attrs(graph: Any, node_id: str) -> dict[str, Any] | None:
    if node_id in graph:
        return dict(graph.nodes[node_id])

    target_name = node_id.split(".")[-1]
    for candidate_id, attrs in graph.nodes(data=True):
        if candidate_id == target_name or str(candidate_id).endswith(f".{target_name}"):
            return dict(attrs)
    return None


def _tree_sitter_range(
    resolved_path: str,
    node_id: str,
    language: str,
) -> tuple[int | None, int | None]:
    try:
        analyzer: Any
        if language == "typescript":
            from analyst.languages.typescript import TypeScriptAnalyzer

            analyzer = TypeScriptAnalyzer()
        else:
            from analyst.languages.javascript import JavaScriptAnalyzer

            analyzer = JavaScriptAnalyzer()

        analysis = analyzer.analyze_file(
            resolved_path,
            os.path.dirname(resolved_path),
            local_modules_override=frozenset(),
        )
    except Exception:
        logger.info(
            "Snippet analyzer fallback failed for %s", resolved_path, exc_info=True
        )
        return None, None

    if analysis is None:
        return None, None
    attrs = _find_graph_node_attrs(analysis.graph, node_id)
    if attrs is None:
        return None, None
    return attrs.get("lineno"), attrs.get("end_lineno")


def extract_snippet(
    file_path: str | None,
    node_id: str | None,
    *,
    language: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
) -> tuple[str, int | None, int | None, str | None]:
    """
    Robustly extracts the source code of a function/class from *file_path*
    whose name matches the last segment of *node_id* (e.g. "MyClass.my_func"
    -> looks for "my_func").

    Returns a tuple of:
      (code_string, start_line, end_line, full_source)
    where start_line and end_line are 1-indexed.
    """
    if not file_path or not node_id:
        return (
            f"# External or Built-in: {node_id}\n"
            "# (No source code available, please explain based on name/context.)",
            None,
            None,
            None,
        )

    resolved = os.path.realpath(file_path)

    if not is_safe_path(resolved):
        if ".claude" in resolved or (file_path and ".claude" in file_path):
            if os.path.isfile(resolved):
                raise HTTPException(
                    status_code=403, detail="Access denied: unsafe file path"
                )
            return f"# Source for {node_id} (External/Built-in)", None, None, None
        raise HTTPException(status_code=403, detail="Access denied: unsafe file path")

    if not os.path.isfile(resolved):
        return (
            f"# Source unavailable for {node_id}\n"
            "# The uploaded source file is no longer available. Please re-upload the project to view and explain this node with source code.",
            None,
            None,
            None,
        )

    try:
        mtime = os.path.getmtime(resolved)
    except OSError:
        mtime = 0.0

    normalized_language = _normalize_language(language, resolved)
    source, source_lines, read_error = _get_source_text(resolved, mtime)
    if read_error:
        if source is not None:
            return read_error, None, None, source
        return read_error, None, None, None
    assert source is not None
    assert source_lines is not None

    if node_id.startswith("module:"):
        snippet, start, end = _module_snippet(source, source_lines)
        return snippet, start, end, source

    metadata_snippet, metadata_start, metadata_end = _slice_lines(
        source, source_lines, start_line, end_line
    )
    if metadata_snippet is not None:
        return metadata_snippet, metadata_start, metadata_end, source

    if normalized_language in JS_LANGUAGES:
        fallback_start, fallback_end = _tree_sitter_range(
            resolved, node_id, normalized_language
        )
        fallback_snippet, fallback_start_line, fallback_end_line = _slice_lines(
            source,
            source_lines,
            fallback_start,
            fallback_end,
        )
        if fallback_snippet is not None:
            return fallback_snippet, fallback_start_line, fallback_end_line, source
        safe_file_path = os.path.basename(file_path) if file_path else "unknown"
        return (
            f"# Code for '{node_id}' not found in {safe_file_path} (analysis mismatch).",
            None,
            None,
            source,
        )

    source, tree, lines, nodes, error = _get_parsed_ast(resolved, mtime)

    if error:
        if source is not None:
            return error, None, None, source
        return error, None, None, None

    # At this point source, tree, lines, and nodes are guaranteed non-None (no error path)
    assert source is not None
    assert tree is not None
    assert lines is not None
    assert nodes is not None

    target_name = node_id.split(".")[-1]

    if target_name in nodes:
        lineno, end_lineno = nodes[target_name]
        start = lineno - 1
        end = end_lineno or len(lines)
        return "\n".join(lines[start:end]), lineno, end_lineno, source

    safe_file_path = os.path.basename(file_path) if file_path else "unknown"
    return (
        f"# Code for '{node_id}' not found in {safe_file_path} (analysis mismatch).",
        None,
        None,
        source,
    )
