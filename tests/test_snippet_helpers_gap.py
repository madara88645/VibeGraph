"""Direct unit coverage for the pure line-slicing / graph-lookup helpers in
app/utils/snippet.py, which previously had no dedicated test — only
exercised indirectly through the full extract_snippet() integration tests
in test_snippet.py.

_slice_lines turns a (start_line, end_line) pair into a source substring,
with several boundary conditions (start<1, end<start, out-of-range end,
trailing-newline preservation) that _get_parsed_ast's caller-supplied
metadata can trigger. _find_graph_node_attrs looks up a node in a networkx
call graph by exact id or by suffix-matching the last dotted segment, which
is how JS/TS fallback snippet extraction locates tree-sitter node metadata.
_module_snippet is the trivial one-liner used for `module:`-prefixed node
ids. A bug in any of these would silently return the wrong snippet (or the
wrong line numbers) without raising an error.
"""

import unittest

import networkx as nx

from app.utils.snippet import _find_graph_node_attrs, _module_snippet, _slice_lines


class TestSliceLines(unittest.TestCase):
    def test_start_or_end_none_returns_all_none(self):
        self.assertEqual(_slice_lines("a\nb\nc", ["a", "b", "c"], None, 2), (None, None, None))
        self.assertEqual(_slice_lines("a\nb\nc", ["a", "b", "c"], 1, None), (None, None, None))

    def test_start_below_one_returns_all_none(self):
        self.assertEqual(
            _slice_lines("a\nb\nc", ["a", "b", "c"], 0, 2), (None, None, None)
        )

    def test_end_before_start_returns_all_none(self):
        self.assertEqual(
            _slice_lines("a\nb\nc", ["a", "b", "c"], 3, 2), (None, None, None)
        )

    def test_start_beyond_line_count_returns_all_none(self):
        self.assertEqual(
            _slice_lines("a\nb\nc", ["a", "b", "c"], 5, 6), (None, None, None)
        )

    def test_normal_slice_within_bounds(self):
        result = _slice_lines("a\nb\nc", ["a", "b", "c"], 1, 2)
        self.assertEqual(result, ("a\nb", 1, 2))

    def test_single_line_slice(self):
        result = _slice_lines("a\nb\nc", ["a", "b", "c"], 2, 2)
        self.assertEqual(result, ("b", 2, 2))

    def test_end_beyond_line_count_is_clamped(self):
        result = _slice_lines("a\nb\nc", ["a", "b", "c"], 2, 100)
        # safe_end clamps to len(lines) == 3; no trailing newline because the
        # source string itself doesn't end with one.
        self.assertEqual(result, ("b\nc", 2, 3))

    def test_start_equal_to_line_count_is_allowed(self):
        result = _slice_lines("a\nb\nc", ["a", "b", "c"], 3, 3)
        self.assertEqual(result, ("c", 3, 3))

    def test_trailing_newline_preserved_when_slice_reaches_last_line(self):
        source = "a\nb\nc\n"
        lines = source.splitlines()  # ["a", "b", "c"] -- trailing "" dropped
        result = _slice_lines(source, lines, 1, 3)
        self.assertEqual(result, ("a\nb\nc\n", 1, 3))

    def test_trailing_newline_not_added_when_slice_stops_short(self):
        source = "a\nb\nc\n"
        lines = source.splitlines()
        result = _slice_lines(source, lines, 1, 2)
        # safe_end (2) != len(lines) (3), so no trailing newline is appended
        # even though the full source ends with one.
        self.assertEqual(result, ("a\nb", 1, 2))

    def test_no_trailing_newline_in_source_means_none_appended(self):
        source = "a\nb\nc"  # no trailing newline
        lines = source.splitlines()
        result = _slice_lines(source, lines, 1, 3)
        self.assertEqual(result, ("a\nb\nc", 1, 3))


class TestModuleSnippet(unittest.TestCase):
    def test_returns_full_source_and_line_span(self):
        source = "a\nb\nc"
        result = _module_snippet(source, ["a", "b", "c"])
        self.assertEqual(result, (source, 1, 3))

    def test_empty_lines_falls_back_to_span_of_one(self):
        result = _module_snippet("", [])
        self.assertEqual(result, ("", 1, 1))


class TestFindGraphNodeAttrs(unittest.TestCase):
    def test_exact_id_match(self):
        graph = nx.DiGraph()
        graph.add_node("mod.Foo.bar", lineno=10, type="function")
        result = _find_graph_node_attrs(graph, "mod.Foo.bar")
        self.assertEqual(result, {"lineno": 10, "type": "function"})

    def test_exact_match_takes_priority_over_suffix_match(self):
        graph = nx.DiGraph()
        graph.add_node("bar", lineno=1, type="exact")
        graph.add_node("mod.Foo.bar", lineno=2, type="suffix")
        result = _find_graph_node_attrs(graph, "bar")
        self.assertEqual(result, {"lineno": 1, "type": "exact"})

    def test_suffix_match_on_dotted_candidate(self):
        graph = nx.DiGraph()
        graph.add_node("mod.Foo.bar", lineno=5, type="function")
        # "unknown_mod.bar" isn't in the graph, but its last segment "bar"
        # matches the tail of "mod.Foo.bar".
        result = _find_graph_node_attrs(graph, "unknown_mod.bar")
        self.assertEqual(result, {"lineno": 5, "type": "function"})

    def test_bare_candidate_id_equal_to_target_name_matches(self):
        graph = nx.DiGraph()
        graph.add_node("bar", lineno=7, type="function")
        result = _find_graph_node_attrs(graph, "mod.bar")
        self.assertEqual(result, {"lineno": 7, "type": "function"})

    def test_no_match_returns_none(self):
        graph = nx.DiGraph()
        graph.add_node("mod.Foo.baz", lineno=1, type="function")
        self.assertIsNone(_find_graph_node_attrs(graph, "mod.bar"))

    def test_empty_graph_returns_none(self):
        graph = nx.DiGraph()
        self.assertIsNone(_find_graph_node_attrs(graph, "anything"))

    def test_first_inserted_suffix_match_wins(self):
        graph = nx.DiGraph()
        graph.add_node("mod.One.bar", lineno=1, type="first")
        graph.add_node("mod.Two.bar", lineno=2, type="second")
        result = _find_graph_node_attrs(graph, "unknown.bar")
        self.assertEqual(result, {"lineno": 1, "type": "first"})


if __name__ == "__main__":
    unittest.main()
