"""Direct unit tests for pure helpers in app/utils/snippet.py that were
previously only exercised indirectly through extract_snippet() integration
tests: _slice_lines (line-range slicing with boundary clamping) and
_find_graph_node_attrs (graph-node lookup with suffix-match fallback).
"""
import networkx as nx

from app.utils.snippet import _find_graph_node_attrs, _slice_lines


# --- _slice_lines -----------------------------------------------------


def test_slice_lines_basic_range():
    source = "a\nb\nc\nd\n"
    lines = source.splitlines()
    snippet, start, end = _slice_lines(source, lines, 2, 3)
    assert snippet == "b\nc"
    assert start == 2
    assert end == 3


def test_slice_lines_none_start_returns_none_triplet():
    source = "a\nb\n"
    lines = source.splitlines()
    assert _slice_lines(source, lines, None, 2) == (None, None, None)


def test_slice_lines_none_end_returns_none_triplet():
    source = "a\nb\n"
    lines = source.splitlines()
    assert _slice_lines(source, lines, 1, None) == (None, None, None)


def test_slice_lines_start_below_one_is_invalid():
    source = "a\nb\n"
    lines = source.splitlines()
    assert _slice_lines(source, lines, 0, 1) == (None, None, None)


def test_slice_lines_end_before_start_is_invalid():
    source = "a\nb\nc\n"
    lines = source.splitlines()
    assert _slice_lines(source, lines, 3, 2) == (None, None, None)


def test_slice_lines_start_beyond_file_length_is_invalid():
    source = "a\nb\n"
    lines = source.splitlines()
    assert _slice_lines(source, lines, 5, 6) == (None, None, None)


def test_slice_lines_end_clamped_to_file_length():
    source = "a\nb\nc\n"
    lines = source.splitlines()
    snippet, start, end = _slice_lines(source, lines, 2, 100)
    assert start == 2
    assert end == 3  # clamped to len(lines)
    # Trailing newline is appended because the clamped slice reaches EOF.
    assert snippet == "b\nc\n"


def test_slice_lines_trailing_newline_preserved_when_slice_reaches_end():
    source = "a\nb\nc\n"
    lines = source.splitlines()
    snippet, _, end = _slice_lines(source, lines, 1, 3)
    assert end == 3
    assert snippet == "a\nb\nc\n"


def test_slice_lines_trailing_newline_not_added_when_slice_is_partial():
    source = "a\nb\nc\n"
    lines = source.splitlines()
    snippet, _, end = _slice_lines(source, lines, 1, 2)
    assert end == 2
    assert snippet == "a\nb"


def test_slice_lines_single_line_selection():
    source = "only line\n"
    lines = source.splitlines()
    snippet, start, end = _slice_lines(source, lines, 1, 1)
    assert snippet == "only line\n"
    assert start == 1
    assert end == 1


# --- _find_graph_node_attrs --------------------------------------------


def _make_graph():
    graph = nx.DiGraph()
    graph.add_node("pkg.module.func", type="function", lineno=10)
    graph.add_node("pkg.module.OtherClass.method", type="method", lineno=20)
    return graph


def test_find_graph_node_attrs_exact_id_match():
    graph = _make_graph()
    attrs = _find_graph_node_attrs(graph, "pkg.module.func")
    assert attrs is not None
    assert attrs["type"] == "function"
    assert attrs["lineno"] == 10


def test_find_graph_node_attrs_suffix_match_by_short_name():
    graph = _make_graph()
    attrs = _find_graph_node_attrs(graph, "func")
    assert attrs is not None
    assert attrs["type"] == "function"


def test_find_graph_node_attrs_suffix_match_dotted_fallback():
    graph = _make_graph()
    # "func" is the last component of "pkg.module.func"; a dotted lookup for
    # a suffix that only exists as ".method" should resolve via endswith.
    attrs = _find_graph_node_attrs(graph, "OtherClass.method")
    assert attrs is not None
    assert attrs["type"] == "method"


def test_find_graph_node_attrs_no_match_returns_none():
    graph = _make_graph()
    assert _find_graph_node_attrs(graph, "does.not.exist") is None


def test_find_graph_node_attrs_returns_a_copy_not_the_live_view():
    graph = _make_graph()
    attrs = _find_graph_node_attrs(graph, "pkg.module.func")
    attrs["type"] = "mutated"
    assert graph.nodes["pkg.module.func"]["type"] == "function"
