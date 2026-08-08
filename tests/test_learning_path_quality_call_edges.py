"""Direct unit coverage for app.services.learning_path_quality pure helpers.

`_call_edges` flattens the adjacency map into (caller, callee) pairs and
`_ordered_node_ids` extracts the step ordering from raw step dicts. Both
feed `assess_learning_path` and `repair_caller_before_callee`, but were
previously only exercised indirectly through those higher-level functions.
"""

from app.services.learning_path_quality import _call_edges, _ordered_node_ids


class TestCallEdges:
    def test_flattens_single_source_multiple_targets(self):
        outgoing = {"main": ["load_config", "run"]}
        assert _call_edges(outgoing) == [("main", "load_config"), ("main", "run")]

    def test_flattens_multiple_sources(self):
        outgoing = {"main": ["load_config"], "load_config": ["read_file"]}
        assert _call_edges(outgoing) == [
            ("main", "load_config"),
            ("load_config", "read_file"),
        ]

    def test_empty_outgoing_returns_empty_list(self):
        assert _call_edges({}) == []

    def test_source_with_no_targets_contributes_no_edges(self):
        outgoing = {"leaf": []}
        assert _call_edges(outgoing) == []


class TestOrderedNodeIds:
    def test_extracts_node_ids_in_order(self):
        steps = [{"node_id": "main"}, {"node_id": "load_config"}]
        assert _ordered_node_ids(steps) == ["main", "load_config"]

    def test_skips_steps_missing_node_id(self):
        steps = [{"node_id": "main"}, {"step": 2}, {"node_id": "run"}]
        assert _ordered_node_ids(steps) == ["main", "run"]

    def test_skips_non_string_node_id(self):
        steps = [{"node_id": "main"}, {"node_id": 123}, {"node_id": None}]
        assert _ordered_node_ids(steps) == ["main"]

    def test_skips_empty_string_node_id(self):
        steps = [{"node_id": ""}, {"node_id": "main"}]
        assert _ordered_node_ids(steps) == ["main"]

    def test_empty_steps_returns_empty_list(self):
        assert _ordered_node_ids([]) == []
