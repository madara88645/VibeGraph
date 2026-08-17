"""Direct unit tests for app/services/learning_path_quality.py's small
adjacency/id-extraction helpers, which previously had no dedicated test —
only exercised indirectly through assess_learning_path in
test_learning_path_quality.py.

_call_edges flattens an {source: [targets]} outgoing-adjacency dict into a
flat list of (source, target) edge tuples, consumed by
assess_learning_path's caller-before-callee ordering check. _ordered_node_ids
extracts the ordered list of node_id strings from a learning-path steps
list, filtering out steps with a missing/non-string/empty node_id -- a bug
here would silently let a malformed step corrupt position tracking instead
of raising.

Both are pure functions with no I/O.
"""

from app.services.learning_path_quality import _call_edges, _ordered_node_ids


class TestCallEdges:
    def test_empty_dict_returns_empty_list(self):
        assert _call_edges({}) == []

    def test_single_source_single_target(self):
        assert _call_edges({"a": ["b"]}) == [("a", "b")]

    def test_single_source_multiple_targets_preserves_order(self):
        assert _call_edges({"a": ["b", "c", "d"]}) == [("a", "b"), ("a", "c"), ("a", "d")]

    def test_multiple_sources_flatten_in_dict_iteration_order(self):
        outgoing = {"a": ["x"], "b": ["y", "z"]}
        assert _call_edges(outgoing) == [("a", "x"), ("b", "y"), ("b", "z")]

    def test_source_with_empty_target_list_contributes_no_edges(self):
        assert _call_edges({"a": [], "b": ["c"]}) == [("b", "c")]

    def test_all_sources_with_empty_target_lists_returns_empty_list(self):
        assert _call_edges({"a": [], "b": []}) == []

    def test_self_loop_target_is_kept(self):
        assert _call_edges({"a": ["a"]}) == [("a", "a")]

    def test_duplicate_targets_are_not_deduplicated(self):
        # _call_edges is a pure flatten -- deduplication (if any) happens
        # upstream in _normalize_graph, not here.
        assert _call_edges({"a": ["b", "b"]}) == [("a", "b"), ("a", "b")]


class TestOrderedNodeIds:
    def test_empty_steps_returns_empty_list(self):
        assert _ordered_node_ids([]) == []

    def test_extracts_node_id_in_order(self):
        steps = [{"node_id": "a"}, {"node_id": "b"}, {"node_id": "c"}]
        assert _ordered_node_ids(steps) == ["a", "b", "c"]

    def test_missing_node_id_key_is_skipped(self):
        steps = [{"node_id": "a"}, {"other": "x"}, {"node_id": "c"}]
        assert _ordered_node_ids(steps) == ["a", "c"]

    def test_none_node_id_is_skipped(self):
        steps = [{"node_id": "a"}, {"node_id": None}, {"node_id": "c"}]
        assert _ordered_node_ids(steps) == ["a", "c"]

    def test_empty_string_node_id_is_skipped(self):
        steps = [{"node_id": "a"}, {"node_id": ""}, {"node_id": "c"}]
        assert _ordered_node_ids(steps) == ["a", "c"]

    def test_non_string_node_id_is_skipped(self):
        steps = [{"node_id": "a"}, {"node_id": 123}, {"node_id": ["b"]}, {"node_id": "c"}]
        assert _ordered_node_ids(steps) == ["a", "c"]

    def test_duplicate_node_ids_are_preserved_not_deduplicated(self):
        # Duplicate detection (for complete_and_unique) happens in the
        # caller, not here -- this is a straight extraction pass.
        steps = [{"node_id": "a"}, {"node_id": "a"}]
        assert _ordered_node_ids(steps) == ["a", "a"]

    def test_extra_keys_on_step_are_ignored(self):
        steps = [{"node_id": "a", "step_number": 1, "reason": "why"}]
        assert _ordered_node_ids(steps) == ["a"]

    def test_all_invalid_node_ids_returns_empty_list(self):
        steps = [{"node_id": None}, {"node_id": ""}, {"node_id": 5}, {}]
        assert _ordered_node_ids(steps) == []
