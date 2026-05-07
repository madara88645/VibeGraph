"""Pluggable language analyzers.

Each language plugin parses files of one or more extensions and produces a
``FileAnalysis`` (subgraph + pending calls + imports) that the orchestrator
in ``analyst.analyzer.CodeAnalyzer`` composes into the final graph.

The registry is populated at import time from the concrete plugin modules.
``get_analyzer_for_path`` returns ``None`` for unsupported extensions, which
the orchestrator treats as "skip silently" (the same way it used to skip
non-``.py`` files).
"""

from __future__ import annotations

import os
from typing import Optional

from analyst.languages.base import FileAnalysis, LanguageAnalyzer, ParseError
from analyst.languages.javascript import JavaScriptAnalyzer
from analyst.languages.python import PythonAnalyzer
from analyst.languages.typescript import TypeScriptAnalyzer

__all__ = [
    "FileAnalysis",
    "LanguageAnalyzer",
    "ParseError",
    "all_extensions",
    "all_languages",
    "get_analyzer_for_path",
]


_REGISTRY: tuple[LanguageAnalyzer, ...] = (
    PythonAnalyzer(),
    JavaScriptAnalyzer(),
    TypeScriptAnalyzer(),
)

_BY_EXTENSION: dict[str, LanguageAnalyzer] = {}
for _analyzer in _REGISTRY:
    for _ext in _analyzer.extensions:
        _BY_EXTENSION[_ext.lower()] = _analyzer


def get_analyzer_for_path(path: str) -> Optional[LanguageAnalyzer]:
    ext = os.path.splitext(path)[1].lower()
    return _BY_EXTENSION.get(ext)


def all_languages() -> list[dict]:
    return [
        {
            "id": a.language_id,
            "label": a.display_label,
            "extensions": list(a.extensions),
        }
        for a in _REGISTRY
    ]


def all_extensions() -> tuple[str, ...]:
    return tuple(sorted(_BY_EXTENSION.keys()))
