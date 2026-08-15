"""Direct unit coverage for the pure flattening/filtering helpers in
app/services/learning_path_quality.py, which previously had no dedicated
test — only exercised indirectly through assess_learning_path() and
repair_caller_before_callee() integration tests in
test_learning_path_quality.py.

_call_edges flattens an ``outgoing: dict[str, list[str]]`` adjacency map
into ``(source, target)`` tuples used to check caller-before-callee
ordering. _ordered_node_ids extracts/filters valid ``node_id`` strings from
a steps list, skipping non-string or empty ids so a malformed step can't
silently corrupt position tracking. A bug in either would let bad data flow
into the quality checks without raising an error.
"""

import unittest

from app.services.learning_path_quality import _call_edges, _ordered_node_ids


class TestCallEdges(unittest.TestCase):
    def test_empty_dict_returns_empty_list(self):
        self.assertEqual(_call_edges({}), [])

    def test_single_source_multiple_targets(self):
        result = _call_edges({"a": ["b", "c"]})
        self.assertEqual(result, [("a", "b"), ("a", "c")])

    def test_multiple_sources_preserve_dict_order(self):
        result = _call_edges({"a": ["b"], "c": ["d", "e"]})
        self.assertEqual(result, [("a", "b"), ("c", "d"), ("c", "e")])

    def test_source_with_empty_target_list_contributes_no_edges(self):
        result = _call_edges({"a": [], "b": ["c"]})
        self.assertEqual(result, [("b", "c")])

    def test_all_sources_with_empty_targets_returns_empty_list(self):
        self.assertEqual(_call_edges({"a": [], "b": []}), [])

    def test_target_order_within_source_is_preserved(self):
        result = _call_edges({"a": ["z", "y", "x"]})
        self.assertEqual(result, [("a", "z"), ("a", "y"), ("a", "x")])


class TestOrderedNodeIds(unittest.TestCase):
    def test_empty_steps_returns_empty_list(self):
        self.assertEqual(_ordered_node_ids([]), [])

    def test_valid_string_ids_are_extracted_in_order(self):
        steps = [{"node_id": "a"}, {"node_id": "b"}, {"node_id": "c"}]
        self.assertEqual(_ordered_node_ids(steps), ["a", "b", "c"])

    def test_missing_node_id_key_is_skipped(self):
        steps = [{"node_id": "a"}, {"reason": "no id here"}, {"node_id": "c"}]
        self.assertEqual(_ordered_node_ids(steps), ["a", "c"])

    def test_non_string_node_id_is_skipped(self):
        steps = [{"node_id": "a"}, {"node_id": 42}, {"node_id": None}, {"node_id": "d"}]
        self.assertEqual(_ordered_node_ids(steps), ["a", "d"])

    def test_empty_string_node_id_is_skipped(self):
        steps = [{"node_id": "a"}, {"node_id": ""}, {"node_id": "c"}]
        self.assertEqual(_ordered_node_ids(steps), ["a", "c"])

    def test_all_invalid_ids_returns_empty_list(self):
        steps = [{"node_id": None}, {"node_id": 1}, {"node_id": ""}, {}]
        self.assertEqual(_ordered_node_ids(steps), [])

    def test_duplicate_ids_are_kept_not_deduped(self):
        # Deduplication is the caller's concern (assess_learning_path uses
        # this to detect duplicates); the helper itself must not filter them.
        steps = [{"node_id": "a"}, {"node_id": "a"}]
        self.assertEqual(_ordered_node_ids(steps), ["a", "a"])


if __name__ == "__main__":
    unittest.main()
