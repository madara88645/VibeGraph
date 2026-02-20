"""Python AST-based code analyzer.

Walks a Python project directory, parses each .py file with the ast module,
and builds an in-memory call graph containing:

  - Nodes: functions, classes, and script entry-points
  - Edges: call relationships between them
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class NodeInfo:
    id: str
    label: str
    node_type: str          # "function" | "class" | "entry"
    file: str
    lineno: int
    source: str = ""        # raw source lines for that function/class


@dataclass
class EdgeInfo:
    source: str
    target: str
    cross_file: bool = False


@dataclass
class CallGraph:
    nodes: Dict[str, NodeInfo] = field(default_factory=dict)
    edges: List[EdgeInfo] = field(default_factory=list)


class _FileVisitor(ast.NodeVisitor):
    """Visits a single Python file and collects nodes/calls."""

    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.nodes: Dict[str, NodeInfo] = {}
        self.calls: List[tuple] = []           # (caller_id, callee_name)
        self._scope_stack: List[str] = []      # stack of current scope ids

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _qualified_id(self, name: str) -> str:
        return f"{self.file_path}::{name}"

    def _current_scope(self) -> Optional[str]:
        return self._scope_stack[-1] if self._scope_stack else None

    def _extract_source(self, node: ast.AST) -> str:
        start = node.lineno - 1
        end = node.end_lineno if hasattr(node, "end_lineno") else start + 1
        return "".join(self.source_lines[start:end])

    # ------------------------------------------------------------------
    # Visitors
    # ------------------------------------------------------------------

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        node_id = self._qualified_id(node.name)
        self.nodes[node_id] = NodeInfo(
            id=node_id,
            label=node.name,
            node_type="function",
            file=self.file_path,
            lineno=node.lineno,
            source=self._extract_source(node),
        )
        self._scope_stack.append(node_id)
        self.generic_visit(node)
        self._scope_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        node_id = self._qualified_id(node.name)
        self.nodes[node_id] = NodeInfo(
            id=node_id,
            label=node.name,
            node_type="class",
            file=self.file_path,
            lineno=node.lineno,
            source=self._extract_source(node),
        )
        self._scope_stack.append(node_id)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        caller = self._current_scope()
        if caller is None:
            self.generic_visit(node)
            return

        # Resolve callee name
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee_name = node.func.attr
        else:
            callee_name = None

        if callee_name:
            self.calls.append((caller, callee_name))

        self.generic_visit(node)


class CodeAnalyzer:
    """Analyzes a Python project directory and builds a CallGraph."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.graph = CallGraph()

    def analyze(self) -> CallGraph:
        visitors: List[_FileVisitor] = []

        for py_file in sorted(self.project_path.rglob("*.py")):
            # Skip common non-project directories
            parts = py_file.parts
            if any(p in parts for p in ("__pycache__", ".venv", "venv", "node_modules")):
                continue

            rel_path = str(py_file.relative_to(self.project_path))
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=rel_path)
            except (SyntaxError, UnicodeDecodeError):
                continue

            source_lines = source.splitlines(keepends=True)
            visitor = _FileVisitor(rel_path, source_lines)
            visitor.visit(tree)
            visitors.append(visitor)

            # Add nodes from this file
            for node in visitor.nodes.values():
                self.graph.nodes[node.id] = node

            # Detect top-level entry point (if __name__ == "__main__")
            for stmt in tree.body:
                if (
                    isinstance(stmt, ast.If)
                    and isinstance(stmt.test, ast.Compare)
                    and isinstance(stmt.test.left, ast.Name)
                    and stmt.test.left.id == "__name__"
                ):
                    entry_id = f"{rel_path}::__main__"
                    self.graph.nodes[entry_id] = NodeInfo(
                        id=entry_id,
                        label="__main__",
                        node_type="entry",
                        file=rel_path,
                        lineno=stmt.lineno,
                        source="".join(source_lines[stmt.lineno - 1 : getattr(stmt, "end_lineno", stmt.lineno)]),
                    )

        # Build name → id lookup
        name_to_ids: Dict[str, List[str]] = {}
        for node_id, node in self.graph.nodes.items():
            name_to_ids.setdefault(node.label, []).append(node_id)

        # Resolve calls to edges
        seen_edges: Set[tuple] = set()
        for visitor in visitors:
            caller_file = visitor.file_path
            for caller_id, callee_name in visitor.calls:
                if callee_name not in name_to_ids:
                    continue
                for target_id in name_to_ids[callee_name]:
                    if (caller_id, target_id) in seen_edges:
                        continue
                    seen_edges.add((caller_id, target_id))
                    target_node = self.graph.nodes[target_id]
                    self.graph.edges.append(
                        EdgeInfo(
                            source=caller_id,
                            target=target_id,
                            cross_file=target_node.file != caller_file,
                        )
                    )

        return self.graph
