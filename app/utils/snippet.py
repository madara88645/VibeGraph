"""Source code snippet extraction from Python files."""

import ast
import functools
import os

from fastapi import HTTPException

from app.utils.security import is_safe_path


@functools.lru_cache(maxsize=128)
def _get_parsed_ast_data(
    resolved_path: str, mtime: float
) -> tuple[
    str | None,
    list[str] | None,
    dict[str, tuple[int, int | None]] | None,
    str | None,
]:
    """
    Parses the file and caches the source, split lines, and a mapping
    of node names to their start and end line numbers.
    """
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        return None, None, None, f"# Error reading file: {e}"

    try:
        tree = ast.parse(source, filename=resolved_path)
    except SyntaxError as e:
        return source, None, None, f"# Syntax error in {resolved_path}: {e}"

    lines = source.splitlines()
    nodes = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name not in nodes:
                nodes[node.name] = (node.lineno, node.end_lineno)

    return source, lines, nodes, None


def extract_snippet(
    file_path: str | None, node_id: str | None
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
        raise HTTPException(status_code=403, detail="Access denied: unsafe file path")

    if not os.path.isfile(resolved):
        return f"# Source for {node_id} (External/Built-in)", None, None, None

    try:
        mtime = os.path.getmtime(resolved)
    except OSError:
        mtime = 0.0

    source, lines, nodes, error = _get_parsed_ast_data(resolved, mtime)

    if error:
        if source is not None:
            return error, None, None, source
        return error, None, None, None

    # At this point all are guaranteed non-None (no error path)
    assert source is not None
    assert lines is not None
    assert nodes is not None

    target_name = node_id.split(".")[-1]

    # ⚡ Bolt: Fast lookup from cached dictionary instead of full AST walk
    if target_name in nodes:
        start_lineno, end_lineno = nodes[target_name]
        start = start_lineno - 1
        end = end_lineno or len(lines)
        return "\n".join(lines[start:end]), start_lineno, end_lineno, source

    return (
        f"# Code for '{node_id}' not found in {file_path} (analysis mismatch).",
        None,
        None,
        source,
    )
