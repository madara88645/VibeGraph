"""Direct unit tests for the pure scoring/classification/graph-normalization
helpers in app/services/learning_path.py.

The existing learning-path test files (test_learning_path_logic.py,
test_learning_path_service.py, test_learning_path_quality.py) all drive
these helpers indirectly through `build_learning_path`, and every sample
node in those files sets `entry_point` / `public_api` as an explicit
boolean. That never exercises the name/filename-based *fallback* heuristics
in `_is_entry_point` / `_is_public_api`, never asserts the exact `_reason`
text for each signal combination, never exercises `nesting_depth` /
`dependency_count` in `_complexity_penalty`, and never calls
`_normalize_graph` with malformed input (duplicate edges, dangling edges,
missing/invalid node ids). This file covers those gaps directly.
"""

from app.services.learning_path import (
    _complexity_penalty,
    _is_entry_point,
    _is_public_api,
    _normalize_graph,
    _reason,
    normalize_graph,
)


# ---------------------------------------------------------------------------
# _complexity_penalty
# ---------------------------------------------------------------------------
class TestComplexityPenalty:
    def test_empty_data_is_zero(self):
        assert _complexity_penalty({}) == 0.0

    def test_combines_loc_nesting_and_dependencies(self):
        # 50 * 0.1 + 2 * 4.0 + 3 * 2.0 = 5.0 + 8.0 + 6.0 = 19.0
        data = {"loc": 50, "nesting_depth": 2, "dependency_count": 3}
        assert _complexity_penalty(data) == 19.0

    def test_result_is_capped_at_forty(self):
        assert _complexity_penalty({"loc": 1000}) == 40.0
        assert _complexity_penalty({"nesting_depth": 100}) == 40.0

    def test_negative_inputs_are_clamped_to_zero(self):
        assert _complexity_penalty({"loc": -10, "nesting_depth": -5}) == 0.0

    def test_missing_fields_default_to_zero(self):
        assert _complexity_penalty({"loc": 20}) == 2.0


# ---------------------------------------------------------------------------
# _is_public_api
# ---------------------------------------------------------------------------
class TestIsPublicApi:
    def test_explicit_true_wins(self):
        assert _is_public_api("n", {"public_api": True}) is True

    def test_explicit_false_wins_even_over_public_looking_name(self):
        assert _is_public_api("n", {"public_api": False, "label": "public_fn"}) is False

    def test_fallback_public_name_has_no_leading_underscore(self):
        assert _is_public_api("n", {"label": "helper"}) is True

    def test_fallback_private_name_has_leading_underscore(self):
        assert _is_public_api("n", {"label": "_priv"}) is False

    def test_fallback_uses_node_id_when_label_missing(self):
        assert _is_public_api("_hidden", {}) is False
        assert _is_public_api("visible", {}) is True

    def test_fallback_checks_only_the_final_dotted_segment(self):
        assert _is_public_api("n", {"label": "module.public_fn"}) is True
        assert _is_public_api("n", {"label": "module._internal"}) is False


# ---------------------------------------------------------------------------
# _is_entry_point
# ---------------------------------------------------------------------------
class TestIsEntryPoint:
    def test_explicit_true_short_circuits(self):
        assert _is_entry_point("n", {"entry_point": True}) is True

    def test_explicit_false_does_not_override_name_heuristic(self):
        # Only `is True` short-circuits; an explicit False just falls
        # through to the same name/file heuristic as if the key were absent.
        assert _is_entry_point("n", {"entry_point": False, "label": "main"}) is True

    def test_name_based_heuristics(self):
        for name in ("main", "run", "app"):
            assert _is_entry_point("n", {"label": name}) is True
        assert _is_entry_point("n", {"label": "foo"}) is False

    def test_filename_based_heuristics(self):
        for filename in ("cli.py", "__main__.py", "main.py", "serve.py"):
            assert _is_entry_point("n", {"label": "foo", "file": filename}) is True

    def test_filename_heuristic_uses_basename(self):
        assert _is_entry_point("n", {"label": "foo", "file": "src/pkg/cli.py"}) is True

    def test_no_match_returns_false(self):
        assert _is_entry_point("n", {"label": "foo", "file": "other.py"}) is False
        assert _is_entry_point("n", {}) is False


# ---------------------------------------------------------------------------
# _reason
# ---------------------------------------------------------------------------
def _signals(**overrides):
    base = {
        "entry_point": False,
        "api_boundary": False,
        "public_api": False,
        "hub_score": 0,
        "side_effect_boundary": False,
    }
    base.update(overrides)
    return base


class TestReason:
    def test_entry_point_reason(self):
        assert "primary entry point" in _reason(_signals(entry_point=True))

    def test_api_boundary_takes_priority_over_public_api(self):
        text = _reason(_signals(api_boundary=True, public_api=True))
        assert "external API boundary" in text
        assert "public-facing API" not in text

    def test_public_api_only_reason(self):
        text = _reason(_signals(public_api=True))
        assert "public-facing API" in text

    def test_hub_score_at_threshold_included(self):
        assert "coordination hub" in _reason(_signals(hub_score=15))

    def test_hub_score_below_threshold_excluded(self):
        text = _reason(_signals(hub_score=14.99))
        assert "coordination hub" not in text
        # No other signal fired either, so it must fall back.
        assert "internal helper" in text

    def test_side_effect_boundary_reason(self):
        assert "side effects" in _reason(_signals(side_effect_boundary=True))

    def test_fallback_reason_when_no_signals_fire(self):
        assert "internal helper" in _reason(_signals())

    def test_combined_signals_join_in_declared_order(self):
        text = _reason(
            _signals(
                entry_point=True,
                api_boundary=True,
                public_api=True,
                hub_score=20,
                side_effect_boundary=True,
            )
        )
        entry_idx = text.index("primary entry point")
        api_idx = text.index("external API boundary")
        hub_idx = text.index("coordination hub")
        side_idx = text.index("side effects")
        assert entry_idx < api_idx < hub_idx < side_idx
        # api_boundary firing means the public_api-only sentence is absent.
        assert "public-facing API" not in text


# ---------------------------------------------------------------------------
# _normalize_graph (aliased publicly as normalize_graph)
# ---------------------------------------------------------------------------
class TestNormalizeGraph:
    def test_public_alias_matches_private_function(self):
        assert normalize_graph is _normalize_graph

    def test_nodes_with_missing_empty_or_non_string_id_are_dropped(self):
        nodes = [
            {"id": "a", "data": {}},
            {"id": "", "data": {}},
            {"id": 123, "data": {}},
            {"data": {}},
        ]
        normalized_nodes, _, incoming = _normalize_graph(nodes, [])
        assert set(normalized_nodes) == {"a"}
        assert incoming == {"a": 0}

    def test_node_data_defaults_to_empty_dict_when_missing_or_not_a_dict(self):
        nodes = [{"id": "a"}, {"id": "b", "data": "not-a-dict"}]
        normalized_nodes, _, _ = _normalize_graph(nodes, [])
        assert normalized_nodes["a"] == {}
        assert normalized_nodes["b"] == {}

    def test_duplicate_edges_are_deduplicated(self):
        nodes = [{"id": "a"}, {"id": "b"}]
        edges = [{"source": "a", "target": "b"}, {"source": "a", "target": "b"}]
        _, outgoing, incoming = _normalize_graph(nodes, edges)
        assert outgoing["a"] == ["b"]
        assert incoming == {"a": 0, "b": 1}

    def test_edges_referencing_unknown_nodes_are_dropped(self):
        nodes = [{"id": "a"}, {"id": "b"}]
        edges = [
            {"source": "a", "target": "unknown"},
            {"source": "unknown", "target": "b"},
            {"source": "a", "target": "b"},
        ]
        _, outgoing, incoming = _normalize_graph(nodes, edges)
        assert outgoing == {"a": ["b"]}
        assert incoming == {"a": 0, "b": 1}

    def test_self_loop_edges_are_kept(self):
        nodes = [{"id": "a"}]
        edges = [{"source": "a", "target": "a"}]
        _, outgoing, incoming = _normalize_graph(nodes, edges)
        assert outgoing["a"] == ["a"]
        assert incoming["a"] == 1

    def test_malformed_edges_missing_source_or_target_are_ignored(self):
        nodes = [{"id": "a"}, {"id": "b"}]
        edges = [{"source": "a"}, {"target": "b"}, {}]
        _, outgoing, incoming = _normalize_graph(nodes, edges)
        assert outgoing == {}
        assert incoming == {"a": 0, "b": 0}

    def test_outgoing_targets_are_sorted(self):
        nodes = [{"id": "x"}, {"id": "z"}, {"id": "m"}, {"id": "a"}]
        edges = [
            {"source": "x", "target": "z"},
            {"source": "x", "target": "a"},
            {"source": "x", "target": "m"},
        ]
        _, outgoing, _ = _normalize_graph(nodes, edges)
        assert outgoing["x"] == ["a", "m", "z"]
