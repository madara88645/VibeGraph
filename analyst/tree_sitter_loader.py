"""Lazy, thread-safe tree-sitter Language singletons.

The grammar packages (``tree_sitter_javascript``, ``tree_sitter_typescript``)
ship prebuilt wheels with a C extension. Loading them is fast but not free,
so each grammar is instantiated once and reused. ``Language`` and ``Parser``
objects are safe to share across threads as long as a parser instance is
not used concurrently — callers should request a fresh ``Parser`` per call
site or guard their parser with a lock.
"""

from __future__ import annotations

import threading
from typing import Callable

from tree_sitter import Language, Parser

_LOCK = threading.Lock()
_LANGUAGES: dict[str, Language] = {}


def _load_javascript() -> Language:
    import tree_sitter_javascript

    return Language(tree_sitter_javascript.language())


def _load_typescript() -> Language:
    import tree_sitter_typescript

    return Language(tree_sitter_typescript.language_typescript())


def _load_tsx() -> Language:
    import tree_sitter_typescript

    return Language(tree_sitter_typescript.language_tsx())


_LOADERS: dict[str, Callable[[], Language]] = {
    "javascript": _load_javascript,
    "typescript": _load_typescript,
    "tsx": _load_tsx,
}


def get_language(name: str) -> Language:
    with _LOCK:
        cached = _LANGUAGES.get(name)
    if cached is not None:
        return cached

    loader = _LOADERS.get(name)
    if loader is None:
        raise ValueError(f"Unknown tree-sitter language: {name!r}")
    lang = loader()

    with _LOCK:
        _LANGUAGES.setdefault(name, lang)
        return _LANGUAGES[name]


def get_parser(name: str) -> Parser:
    """Return a fresh ``Parser`` bound to the requested language. Parsers are
    cheap to construct, so callers should make one per call site rather than
    sharing a single instance across threads.
    """
    return Parser(get_language(name))
