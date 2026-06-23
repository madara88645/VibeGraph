"""Unit tests for snippet._normalize_language.

``_normalize_language`` maps a caller-supplied language hint (with common
aliases) or, failing that, a file extension onto one of VibeGraph's three
supported canonical languages. ``extract_snippet`` relies on it to pick the
right parser, so its alias table and extension fallbacks are worth pinning
down directly — previously only ``extract_snippet`` itself was covered.
"""

import pytest

from app.utils.snippet import _normalize_language


@pytest.mark.parametrize(
    "language",
    ["js", "jsx", "javascript", "JS", "  JavaScript  "],
)
def test_javascript_aliases_normalize(language: str) -> None:
    assert _normalize_language(language, None) == "javascript"


@pytest.mark.parametrize("language", ["ts", "tsx", "typescript", "TypeScript"])
def test_typescript_aliases_normalize(language: str) -> None:
    assert _normalize_language(language, None) == "typescript"


@pytest.mark.parametrize("language", ["py", "python", "PYTHON"])
def test_python_aliases_normalize(language: str) -> None:
    assert _normalize_language(language, None) == "python"


def test_explicit_language_takes_priority_over_extension() -> None:
    # A recognized language hint wins even when the extension disagrees.
    assert _normalize_language("python", "weird.tsx") == "python"


@pytest.mark.parametrize(
    ("file_path", "expected"),
    [
        ("a.js", "javascript"),
        ("a.jsx", "javascript"),
        ("a.mjs", "javascript"),
        ("a.cjs", "javascript"),
        ("a.ts", "typescript"),
        ("a.tsx", "typescript"),
        ("a.py", "python"),
    ],
)
def test_extension_fallback_when_language_missing(
    file_path: str, expected: str
) -> None:
    assert _normalize_language(None, file_path) == expected


def test_unrecognized_extension_falls_back_to_file_ext() -> None:
    # Unknown language string -> drop to extension; ".rs" is unsupported -> None.
    assert _normalize_language("rust", "main.rs") is None


def test_no_language_and_no_path_returns_none() -> None:
    assert _normalize_language(None, None) is None
