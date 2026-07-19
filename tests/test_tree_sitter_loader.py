import threading

import pytest
from tree_sitter import Language, Parser

from analyst.tree_sitter_loader import get_language, get_parser


@pytest.mark.parametrize("name", ["javascript", "typescript", "tsx"])
def test_get_language_returns_a_language_for_each_supported_grammar(name):
    assert isinstance(get_language(name), Language)


def test_get_language_caches_and_returns_the_same_instance():
    first = get_language("javascript")
    second = get_language("javascript")
    assert first is second


def test_get_language_unknown_name_raises_value_error():
    with pytest.raises(ValueError, match="Unknown tree-sitter language"):
        get_language("cobol")


def test_get_language_is_thread_safe_and_yields_one_shared_instance():
    results: list[Language] = []

    def _load():
        results.append(get_language("typescript"))

    threads = [threading.Thread(target=_load) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 8
    assert all(lang is results[0] for lang in results)


def test_get_parser_returns_a_usable_parser_instance():
    parser = get_parser("javascript")
    assert isinstance(parser, Parser)
    tree = parser.parse(b"const x = 1;")
    assert tree.root_node is not None


def test_get_parser_returns_a_fresh_instance_per_call():
    first = get_parser("javascript")
    second = get_parser("javascript")
    assert first is not second


def test_get_parser_unknown_language_raises_value_error():
    with pytest.raises(ValueError, match="Unknown tree-sitter language"):
        get_parser("nope")
