"""Direct unit tests for app/utils/snippet.py's line-slicing and fuzzy
graph-node-lookup helpers, which previously had no dedicated test — only
exercised indirectly through extract_snippet's higher-level integration
tests in test_snippet.py.

_slice_lines converts a (start_line, end_line) pair into a 1-indexed,
boundary-clamped source substring; it is the last line of defense before
returning a snippet to the UI, so an off-by-one here silently shows the
wrong lines rather than raising. _find_graph_node_attrs resolves a node id
to graph node attributes with an exact-match-then-suffix-match fallback,
used when the JS/TS tree-sitter analyzer's node ids don't exactly match the
requested dotted id.

Both are pure functions with no I/O.
"""

import networkx as nx
import pytest

from app.utils.snippet import _find_graph_node_attrs, _slice_lines


LINES = ["line1", "line2", "line3", "line4", "line5"]
SOURCE_NO_TRAILING_NEWLINE = "\n".join(LINES)
SOURCE_WITH_TRAILING_NEWLINE = "\n".join(LINES) + "\n"


class TestSliceLinesHappyPath:
    def test_full_range(self):
        snippet, start, end = _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 1, 5)
        assert snippet == "line1\nline2\nline3\nline4\nline5"
        assert start == 1
        assert end == 5

    def test_middle_subrange(self):
        snippet, start, end = _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 2, 4)
        assert snippet == "line2\nline3\nline4"
        assert start == 2
        assert end == 4

    def test_single_line_range(self):
        snippet, start, end = _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 3, 3)
        assert snippet == "line3"
        assert start == 3
        assert end == 3


class TestSliceLinesNoneInputs:
    def test_start_line_none_returns_none_triple(self):
        assert _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, None, 3) == (None, None, None)

    def test_end_line_none_returns_none_triple(self):
        assert _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 1, None) == (None, None, None)

    def test_both_none_returns_none_triple(self):
        assert _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, None, None) == (None, None, None)


class TestSliceLinesBoundaryClamps:
    def test_start_line_zero_is_invalid(self):
        assert _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 0, 3) == (None, None, None)

    def test_start_line_negative_is_invalid(self):
        assert _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, -1, 3) == (None, None, None)

    def test_end_line_before_start_line_is_invalid(self):
        assert _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 4, 2) == (None, None, None)

    def test_start_line_beyond_file_length_is_invalid(self):
        assert _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 6, 6) == (None, None, None)

    def test_start_line_equal_to_file_length_is_valid(self):
        snippet, start, end = _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 5, 5)
        assert snippet == "line5"
        assert start == 5
        assert end == 5

    def test_end_line_beyond_file_length_is_clamped(self):
        snippet, start, end = _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 4, 100)
        assert snippet == "line4\nline5"
        assert start == 4
        assert end == 5  # clamped to len(lines), not the requested 100

    def test_end_line_equal_to_start_line_zero_boundary(self):
        # start_line < 1 check happens before end_line < start_line, but a
        # start_line of 1 with end_line 1 is the minimal valid range.
        snippet, start, end = _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 1, 1)
        assert snippet == "line1"
        assert start == 1
        assert end == 1


class TestSliceLinesTrailingNewline:
    def test_trailing_newline_preserved_when_slice_reaches_last_line(self):
        snippet, _, safe_end = _slice_lines(SOURCE_WITH_TRAILING_NEWLINE, LINES, 4, 5)
        assert snippet == "line4\nline5\n"
        assert safe_end == 5

    def test_trailing_newline_not_added_when_slice_stops_before_last_line(self):
        snippet, _, safe_end = _slice_lines(SOURCE_WITH_TRAILING_NEWLINE, LINES, 1, 3)
        assert snippet == "line1\nline2\nline3"
        assert safe_end == 3

    def test_no_trailing_newline_in_source_means_none_added(self):
        snippet, _, safe_end = _slice_lines(SOURCE_NO_TRAILING_NEWLINE, LINES, 1, 5)
        assert snippet == "line1\nline2\nline3\nline4\nline5"
        assert not snippet.endswith("\n")

    def test_trailing_newline_added_when_end_line_over_shoots_but_clamps_to_last(self):
        # end_line=100 clamps to safe_end=len(lines)=5, which is the last
        # line, so the trailing-newline branch should still fire.
        snippet, _, safe_end = _slice_lines(SOURCE_WITH_TRAILING_NEWLINE, LINES, 1, 100)
        assert snippet.endswith("\n")
        assert safe_end == 5


class TestSliceLinesEmptyFile:
    def test_empty_lines_list_with_start_line_one_is_out_of_range(self):
        # len(lines) == 0, so start_line=1 > len(lines) -> invalid.
        assert _slice_lines("", [], 1, 1) == (None, None, None)


def _graph_with_nodes(*node_ids_and_attrs):
    graph = nx.DiGraph()
    for node_id, attrs in node_ids_and_attrs:
        graph.add_node(node_id, **attrs)
    return graph


class TestFindGraphNodeAttrsExactMatch:
    def test_exact_match_returns_attrs_copy(self):
        graph = _graph_with_nodes(("foo", {"lineno": 3, "end_lineno": 5}))
        result = _find_graph_node_attrs(graph, "foo")
        assert result == {"lineno": 3, "end_lineno": 5}

    def test_exact_match_is_a_copy_not_a_live_view(self):
        graph = _graph_with_nodes(("foo", {"lineno": 3}))
        result = _find_graph_node_attrs(graph, "foo")
        result["lineno"] = 999
        assert graph.nodes["foo"]["lineno"] == 3

    def test_exact_match_takes_priority_over_suffix_match(self):
        # Both "a.b.foo" (exact) and "foo" (suffix candidate) exist; the
        # exact match must win.
        graph = _graph_with_nodes(
            ("a.b.foo", {"lineno": 1}),
            ("foo", {"lineno": 2}),
        )
        result = _find_graph_node_attrs(graph, "a.b.foo")
        assert result == {"lineno": 1}


class TestFindGraphNodeAttrsSuffixFallback:
    def test_suffix_match_on_dotted_candidate(self):
        graph = _graph_with_nodes(("MyClass.foo", {"lineno": 7}))
        result = _find_graph_node_attrs(graph, "foo")
        assert result == {"lineno": 7}

    def test_candidate_id_equal_to_target_name_matches(self):
        graph = _graph_with_nodes(("foo", {"lineno": 9}))
        result = _find_graph_node_attrs(graph, "Something.foo")
        assert result == {"lineno": 9}

    def test_only_uses_final_dotted_segment_of_requested_id(self):
        graph = _graph_with_nodes(("Other.bar", {"lineno": 1}))
        result = _find_graph_node_attrs(graph, "Something.bar")
        assert result == {"lineno": 1}

    def test_no_match_returns_none(self):
        graph = _graph_with_nodes(("unrelated", {"lineno": 1}))
        assert _find_graph_node_attrs(graph, "missing.name") is None

    def test_empty_graph_returns_none(self):
        graph = nx.DiGraph()
        assert _find_graph_node_attrs(graph, "anything") is None

    def test_suffix_match_does_not_match_substring_without_dot_boundary(self):
        # "notfoo" ends with "foo" as a raw substring but not as
        # ".foo" -- the suffix check requires the dot boundary.
        graph = _graph_with_nodes(("notfoo", {"lineno": 1}))
        assert _find_graph_node_attrs(graph, "foo") is None

    def test_first_matching_candidate_wins_when_multiple_suffix_matches_exist(self):
        # Graph iteration order is insertion order for nx.DiGraph; the
        # function returns on the first suffix match found.
        graph = _graph_with_nodes(
            ("A.foo", {"lineno": 1}),
            ("B.foo", {"lineno": 2}),
        )
        result = _find_graph_node_attrs(graph, "foo")
        assert result == {"lineno": 1}


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
