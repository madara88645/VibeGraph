"""Source code snippet extraction from Python files."""

import ast
import functools
import logging
import os

from fastapi import HTTPException

from analyst.analyzer import MAX_FILE_SIZE
from app.utils.security import is_safe_path

logger = logging.getLogger(__name__)


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
    try:
        if os.path.getsize(resolved_path) > MAX_FILE_SIZE:
            return (
                None,
                None,
                None,
                None,
                f"# Error: File exceeds maximum allowed size ({MAX_FILE_SIZE} bytes).",
            )
        with open(resolved_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError:
        logger.warning("Snippet read failed for %s", resolved_path, exc_info=True)
        return (
            None,
            None,
            None,
            None,
            "# Error reading file. It may be missing or inaccessible.",
        )

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

    # PERFORMANCE OPTIMIZATION (Bolt): Replaced ast.walk() with a targeted BFS traversal
    # that only visits nodes containing a `body` (or `orelse`/`handlers`/`finalbody`/`cases`).
    # This preserves the exact BFS name-shadowing behavior of ast.walk while skipping
    # thousands of irrelevant leaf nodes (like Name, Constant), drastically improving speed.
    from collections import deque

    queue = deque([tree])

    while queue:
        node = queue.popleft()

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name not in nodes:
                nodes[node.name] = (node.lineno, node.end_lineno)

        # Only add children that are part of statement lists (blocks where defs can occur)
        for attr in ("body", "orelse", "handlers", "finalbody", "cases"):
            if hasattr(node, attr):
                val = getattr(node, attr)
                if isinstance(val, list):
                    queue.extend(val)

    return source, tree, lines, nodes, None


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
