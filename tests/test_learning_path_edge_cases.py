"""Edge-case coverage for app/services/learning_path.py that the existing
suites don't exercise: empty input, the max_fan_out/max_fan_in
division-by-zero guards on graphs with no edges, the 3-tier entry-point
fallback on a pure cycle (no entry_point flags, no zero-incoming nodes),
and the _complexity_penalty saturation/flooring behavior.
"""

from app.services.learning_path import _complexity_penalty, build_learning_path


# ---- build_learning_path: empty input ----


def test_build_learning_path_empty_nodes_and_edges_returns_empty_list():
    assert build_learning_path([], []) == []


def test_build_learning_path_nodes_with_no_edges_returns_empty_list_for_no_nodes():
    assert build_learning_path([], [{"source": "a", "target": "b"}]) == []


# ---- build_learning_path: zero-edge graphs (fan-in/fan-out division guards) ----


def test_build_learning_path_isolated_nodes_no_edges_does_not_divide_by_zero():
    nodes = [
        {"id": "a", "data": {"label": "a", "file": "a.py", "loc": 5}},
        {"id": "b", "data": {"label": "b", "file": "b.py", "loc": 5}},
        {"id": "c", "data": {"label": "c", "file": "c.py", "loc": 5}},
    ]
    steps = build_learning_path(nodes, [])

    assert {step["node_id"] for step in steps} == {"a", "b", "c"}
    for step in steps:
        assert step["signals"]["hub_score"] == 0.0
        assert step["signals"]["fan_in"] == 0
        assert step["signals"]["fan_out"] == 0


def test_build_learning_path_single_node_no_edges_is_its_own_entry():
    nodes = [{"id": "solo", "data": {"label": "solo", "file": "solo.py"}}]
    steps = build_learning_path(nodes, [])

    assert len(steps) == 1
    assert steps[0]["node_id"] == "solo"
    assert steps[0]["step"] == 1


# ---- build_learning_path: cyclic graph with no natural entry point ----


def test_build_learning_path_pure_cycle_falls_back_to_all_nodes_and_visits_every_node():
    """A -> B -> C -> A: no entry_point flags and no zero-incoming node, so
    build_learning_path must fall through all three entry-detection tiers
    (explicit entry points, zero-incoming roots, then "all nodes") without
    an infinite loop, and must still visit every node exactly once."""
    nodes = [
        {"id": "a", "data": {"label": "a", "file": "a.py"}},
        {"id": "b", "data": {"label": "b", "file": "b.py"}},
        {"id": "c", "data": {"label": "c", "file": "c.py"}},
    ]
    edges = [
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
        {"source": "c", "target": "a"},
    ]

    steps = build_learning_path(nodes, edges)
    ordered_ids = [step["node_id"] for step in steps]

    assert len(ordered_ids) == 3
    assert set(ordered_ids) == {"a", "b", "c"}
    assert [step["step"] for step in steps] == [1, 2, 3]


def test_build_learning_path_cycle_with_one_tagged_entry_point_visits_every_node_once():
    # A 3-cycle has no ordering that satisfies "caller before callee" for every
    # edge, so the quality-repair pass (see learning_path_quality.py) cannot
    # converge on one canonical order — assert the invariants it *does*
    # guarantee: every node present exactly once, with sequential step numbers.
    nodes = [
        {"id": "a", "data": {"label": "a", "file": "a.py", "entry_point": True}},
        {"id": "b", "data": {"label": "b", "file": "b.py"}},
        {"id": "c", "data": {"label": "c", "file": "c.py"}},
    ]
    edges = [
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
        {"source": "c", "target": "a"},
    ]

    steps = build_learning_path(nodes, edges)
    ordered_ids = [step["node_id"] for step in steps]
    assert sorted(ordered_ids) == ["a", "b", "c"]
    assert [step["step"] for step in steps] == [1, 2, 3]


# ---- _complexity_penalty ----


def test_complexity_penalty_empty_data_is_zero():
    assert _complexity_penalty({}) == 0.0


def test_complexity_penalty_computes_weighted_sum_below_cap():
    data = {"loc": 20, "nesting_depth": 2, "dependency_count": 1}
    # 20*0.1 + 2*4.0 + 1*2.0 = 2.0 + 8.0 + 2.0 = 12.0
    assert _complexity_penalty(data) == 12.0


def test_complexity_penalty_saturates_at_forty():
    data = {"loc": 10000, "nesting_depth": 100, "dependency_count": 100}
    assert _complexity_penalty(data) == 40.0


def test_complexity_penalty_negative_inputs_are_floored_to_zero():
    data = {"loc": -50, "nesting_depth": -5, "dependency_count": -3}
    assert _complexity_penalty(data) == 0.0


def test_complexity_penalty_none_inputs_default_to_zero():
    data = {"loc": None, "nesting_depth": None, "dependency_count": None}
    assert _complexity_penalty(data) == 0.0
