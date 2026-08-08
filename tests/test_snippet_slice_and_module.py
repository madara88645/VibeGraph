"""Direct unit coverage for app.utils.snippet pure line-slicing helpers.

`_slice_lines`, `_module_snippet`, and `_find_graph_node_attrs` are the
pure building blocks `extract_snippet` composes to turn a source file plus
line/node metadata into a returned code snippet. They have no I/O and no
network dependency, but were previously only exercised indirectly through
`extract_snippet` integration tests, so their boundary conditions (empty
files, out-of-range lines, trailing newlines, dotted node-id matching)
were never asserted directly.
"""

import networkx as nx

from app.utils.snippet import _find_graph_node_attrs, _module_snippet, _slice_lines


class TestSliceLines:
    def test_slices_inclusive_line_range(self):
        source = "line1\nline2\nline3\n"
        lines = source.splitlines()
        snippet, start, end = _slice_lines(source, lines, 1, 2)
        assert snippet == "line1\nline2"
        assert start == 1
        assert end == 2

    def test_appends_trailing_newline_when_source_ends_with_one_and_slice_reaches_end(self):
        source = "line1\nline2\nline3\n"
        lines = source.splitlines()
        snippet, start, end = _slice_lines(source, lines, 1, 3)
        assert snippet == "line1\nline2\nline3\n"
        assert (start, end) == (1, 3)

    def test_no_trailing_newline_added_when_source_has_none(self):
        source = "line1\nline2\nline3"
        lines = source.splitlines()
        snippet, start, end = _slice_lines(source, lines, 1, 3)
        assert snippet == "line1\nline2\nline3"

    def test_no_trailing_newline_added_when_slice_does_not_reach_end(self):
        source = "line1\nline2\nline3\n"
        lines = source.splitlines()
        snippet, start, end = _slice_lines(source, lines, 1, 2)
        assert not snippet.endswith("\n")

    def test_none_start_line_returns_none_triple(self):
        assert _slice_lines("a\nb\n", ["a", "b"], None, 2) == (None, None, None)

    def test_none_end_line_returns_none_triple(self):
        assert _slice_lines("a\nb\n", ["a", "b"], 1, None) == (None, None, None)

    def test_start_line_below_one_is_invalid(self):
        assert _slice_lines("a\nb\n", ["a", "b"], 0, 1) == (None, None, None)

    def test_end_before_start_is_invalid(self):
        assert _slice_lines("a\nb\nc\n", ["a", "b", "c"], 3, 1) == (None, None, None)

    def test_start_line_beyond_file_length_is_invalid(self):
        assert _slice_lines("a\nb\n", ["a", "b"], 5, 6) == (None, None, None)

    def test_end_line_beyond_file_length_is_clamped(self):
        source = "a\nb\n"
        lines = source.splitlines()
        snippet, start, end = _slice_lines(source, lines, 1, 100)
        # safe_end clamps to len(lines), which also reaches the end of the
        # source, so the trailing newline is re-appended (see the "appends
        # trailing newline" case above).
        assert snippet == "a\nb\n"
        assert (start, end) == (1, 2)

    def test_single_line_slice(self):
        source = "only\n"
        lines = source.splitlines()
        snippet, start, end = _slice_lines(source, lines, 1, 1)
        # The single line is also the last line, so the trailing newline
        # from the source is preserved.
        assert snippet == "only\n"
        assert (start, end) == (1, 1)


class TestModuleSnippet:
    def test_returns_full_source_with_line_count(self):
        source = "a\nb\nc\n"
        lines = source.splitlines()
        snippet, start, end = _module_snippet(source, lines)
        assert snippet == source
        assert start == 1
        assert end == 3

    def test_empty_file_still_reports_at_least_one_line(self):
        snippet, start, end = _module_snippet("", [])
        assert snippet == ""
        assert start == 1
        assert end == 1

    def test_single_line_file(self):
        snippet, start, end = _module_snippet("only line", ["only line"])
        assert (start, end) == (1, 1)


class TestFindGraphNodeAttrs:
    def _graph(self):
        graph = nx.DiGraph()
        graph.add_node("module.MyClass.my_func", lineno=10, end_lineno=15)
        graph.add_node("module.other_func", lineno=1, end_lineno=3)
        return graph

    def test_exact_node_id_match(self):
        graph = self._graph()
        attrs = _find_graph_node_attrs(graph, "module.MyClass.my_func")
        assert attrs == {"lineno": 10, "end_lineno": 15}

    def test_falls_back_to_dotted_suffix_match(self):
        graph = self._graph()
        attrs = _find_graph_node_attrs(graph, "MyClass.my_func")
        assert attrs == {"lineno": 10, "end_lineno": 15}

    def test_falls_back_to_bare_name_match(self):
        graph = self._graph()
        attrs = _find_graph_node_attrs(graph, "other_func")
        assert attrs == {"lineno": 1, "end_lineno": 3}

    def test_no_match_returns_none(self):
        graph = self._graph()
        assert _find_graph_node_attrs(graph, "does_not_exist") is None

    def test_returns_a_copy_not_the_live_attrs_dict(self):
        graph = self._graph()
        attrs = _find_graph_node_attrs(graph, "module.other_func")
        attrs["lineno"] = 999
        assert graph.nodes["module.other_func"]["lineno"] == 1
