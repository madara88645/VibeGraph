"""Python language plugin.

Wraps the legacy ``ast``-based analyser that lives in ``analyst.analyzer``.
The plugin exposes the multi-language ``LanguageAnalyzer`` contract while
internally delegating to the well-tested ``CallGraphVisitor`` and helpers,
which keeps the 31-test parity suite green during the multi-language pivot.

A future PR may swap the internals for tree-sitter-python without changing
this file's public shape — that's the seam the plugin architecture exists
for.
"""

from __future__ import annotations

import os
from typing import Any

from analyst.languages.base import FileAnalysis


class PythonAnalyzer:
    language_id = "python"
    display_label = "Python"
    extensions: tuple[str, ...] = (".py",)

    @property
    def builtins(self) -> frozenset[str]:
        # Imported lazily to avoid a circular import: analyst.analyzer
        # itself does a lazy import of analyst.languages in its file-walking
        # methods, and we don't want either side to load the other at module
        # import time.
        from analyst.analyzer import PY_BUILTINS

        return PY_BUILTINS

    @property
    def stdlib_modules(self) -> frozenset[str]:
        from analyst.analyzer import STDLIB_MODULES

        return STDLIB_MODULES

    def get_local_modules(self, project_root: str) -> frozenset[str]:
        from analyst.analyzer import CodeAnalyzer

        return CodeAnalyzer._get_local_modules(project_root)

    def module_id_from_path(self, file_path: str, project_root: str | None) -> str:
        from analyst.analyzer import _file_to_module_id

        return _file_to_module_id(file_path, project_root)

    def analyze_file(
        self,
        file_path: str,
        project_root: str | None,
        local_modules_override: frozenset[str] | None = None,
        profile_bucket: dict[str, Any] | None = None,
    ) -> FileAnalysis | None:
        from analyst.analyzer import (
            CallGraphVisitor,
            _extract_imports,
            _parse_cached,
        )
        from analyst.languages.base import ParseError

        # Build a project-relative display name so multi-file uploads with
        # colliding basenames produce distinguishable warnings (matches the
        # legacy orchestrator's per-file ``safe`` behaviour).
        if project_root:
            try:
                rel = os.path.relpath(file_path, project_root)
            except ValueError:
                rel = os.path.basename(file_path)
            safe_name = rel.replace(os.sep, "/")
        else:
            safe_name = os.path.basename(file_path)
        try:
            with open(file_path, "rb") as f:
                source = f.read()
            tree = _parse_cached(source, filename=file_path)
        except SyntaxError as exc:
            raise ParseError(f"Syntax error in {safe_name}") from exc
        except UnicodeDecodeError as exc:
            raise ParseError(f"Could not decode {safe_name}") from exc
        except (ValueError, OSError):
            return None

        visitor = CallGraphVisitor(file_path)
        visitor.visit(tree)

        scan_root = project_root or os.path.dirname(os.path.abspath(file_path))
        local_modules = local_modules_override
        if local_modules is None:
            local_modules = self.get_local_modules(scan_root)
        imports = _extract_imports(tree, local_modules)

        # Stamp language=python on every node the visitor created so the
        # frontend and downstream consumers can render per-language icons.
        for _, node_data in visitor.graph.nodes(data=True):
            node_data.setdefault("language", self.language_id)

        return FileAnalysis(
            file_path=file_path,
            graph=visitor.graph,
            top_level_definitions=list(visitor.top_level_definitions),
            definitions=list(visitor.definitions),
            pending_calls=list(visitor.pending_calls),
            imports=imports,
        )

    # --- helpers exposed for tests / future plugins ---

    def is_top_level_entry_name(self, name: str) -> bool:
        return name in {"main", "run", "app"}

    @staticmethod
    def known_extensions() -> tuple[str, ...]:
        return (".py",)


_PYTHON_DEFINITION_TYPES = frozenset({"function", "class"})


def attach_language_to_node_payload(
    payload: dict[str, Any], language_id: str = "python"
) -> dict[str, Any]:
    """Idempotent helper used by tests/utilities that synthesize raw node
    dicts: ensures a ``language`` key exists without overwriting an existing
    value. Kept here so future Python-specific additions stay co-located.
    """
    payload.setdefault("language", language_id)
    return payload
