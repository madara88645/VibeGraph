"""Language plugin contract.

Each plugin parses one file at a time and returns a ``FileAnalysis``. The
orchestrator (``CodeAnalyzer``) handles file walking, symbol-table merging,
two-pass call resolution, module-node placement, and final cleanup.

The ``pending_calls`` shape is shared across languages on purpose: every
plugin emits dicts of the form

    {"kind": "name",         "name": "foo"}
    {"kind": "self_method",  "name": "foo", "class": "Bar"}
    {"kind": "attribute",    "name": "foo", "base": "obj" | None, "parts": [...]}

so that ``CodeAnalyzer._resolve_call`` can stay language-agnostic and consult
the originating plugin's ``builtins`` / ``stdlib_modules`` for stub typing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import networkx as nx


class ParseError(Exception):
    """Raised by a language plugin when it knows *why* parsing failed and
    wants the orchestrator to surface that reason verbatim instead of the
    generic "Could not parse <file>" fallback. Plugins may also return
    ``None`` from ``analyze_file`` for unrecoverable but uninteresting
    failures (e.g. unreadable bytes) — both paths are valid.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class FileAnalysis:
    """Result of parsing+visiting a single source file.

    Attributes
    ----------
    file_path
        Absolute path of the analysed file (stamped onto every node).
    graph
        Per-file ``nx.DiGraph`` with definitions added; calls are still
        pending and will be resolved into edges by the orchestrator.
    top_level_definitions
        ``[{"name": str, "type": "function"|"class", "lineno": int}, ...]``
        — used to build the cross-file symbol table.
    definitions
        Same shape but includes nested definitions too. Forwarded to the
        public ``analyze_file`` response.
    pending_calls
        ``[(scope_id, info_dict), ...]`` queued during the visit. The
        orchestrator resolves these into typed edges in pass 2.
    imports
        Flat import records used by the call resolver. Each record:
        ``{"kind": "import"|"from", "module": str, "names": [...],
        "asnames": [...], "is_local": bool, "level": int}``.
    """

    file_path: str
    graph: nx.DiGraph
    top_level_definitions: list[dict[str, Any]] = field(default_factory=list)
    definitions: list[dict[str, Any]] = field(default_factory=list)
    pending_calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    imports: list[dict[str, Any]] = field(default_factory=list)


@runtime_checkable
class LanguageAnalyzer(Protocol):
    language_id: str
    display_label: str
    extensions: tuple[str, ...]
    builtins: frozenset[str]
    stdlib_modules: frozenset[str]

    def analyze_file(
        self,
        file_path: str,
        project_root: str | None,
        local_modules_override: frozenset[str] | None = None,
        profile_bucket: dict[str, Any] | None = None,
    ) -> FileAnalysis | None:
        """Parse one file. Return ``None`` (and let the orchestrator log) on
        unrecoverable errors (syntax, decode, OS).

        ``local_modules_override`` lets the orchestrator provide a precomputed
        module set for this run to avoid rescanning the same directory per
        source file. ``profile_bucket`` is an optional mutable dict where
        plugin-specific timing/counter values can be accumulated.
        """
        ...

    def get_local_modules(self, project_root: str) -> frozenset[str]:
        """Discover module identifiers that should count as project-local
        for import resolution. Plugins can return ``frozenset()`` if they
        don't have a useful notion of local modules.
        """
        ...

    def module_id_from_path(self, file_path: str, project_root: str | None) -> str:
        """Return a dotted module id (without the ``module:`` prefix) for a
        source file. Used for module-node placement and cross-file import
        edges.
        """
        ...
