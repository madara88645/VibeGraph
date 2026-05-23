"""Tests for learning path quality checks and repair."""

from app.services.learning_path import build_learning_path, refine_learning_path_with_ai
from app.services.learning_path_quality import (
    apply_learning_path_quality,
    assess_learning_path,
    repair_caller_before_callee,
)
def _sample_nodes():
    return [
        {
            "id": "main",
            "data": {
                "label": "main",
                "file": "repo/main.py",
                "type": "function",
                "entry_point": True,
                "lineno": 10,
                "loc": 12,
                "public_api": True,
            },
        },
        {
            "id": "load_config",
            "data": {
                "label": "load_config",
                "file": "repo/config.py",
                "type": "function",
                "lineno": 4,
                "loc": 8,
                "side_effect_boundary": True,
                "public_api": True,
            },
        },
        {
            "id": "Api.create",
            "data": {
                "label": "Api.create",
                "file": "repo/api.py",
                "type": "function",
                "lineno": 20,
                "loc": 9,
                "api_boundary": True,
                "public_api": True,
            },
        },
        {
            "id": "_normalize",
            "data": {
                "label": "_normalize",
                "file": "repo/internal.py",
                "type": "function",
                "lineno": 2,
                "loc": 4,
                "public_api": False,
            },
        },
    ]


def _sample_edges():
    return [
        {"source": "main", "target": "load_config"},
        {"source": "main", "target": "Api.create"},
        {"source": "Api.create", "target": "_normalize"},
    ]


def test_sample_graph_passes_quality_checks():
    steps = build_learning_path(_sample_nodes(), _sample_edges())
    report = assess_learning_path(steps, _sample_nodes(), _sample_edges())

    assert report.passed
    assert report.caller_before_callee
    assert report.complete_and_unique
    assert report.step_numbers_valid


def test_assess_detects_call_edge_violation():
    nodes = _sample_nodes()
    edges = _sample_edges()
    steps = build_learning_path(nodes, edges)
    bad_steps = list(reversed(steps))

    report = assess_learning_path(bad_steps, nodes, edges)

    assert report.caller_before_callee is False
    assert report.violating_edges
    assert any("caller_before_callee" in item for item in report.violations)


def test_repair_moves_caller_before_callee():
    outgoing = {"main": ["leaf"], "orphan": ["leaf"]}
    repaired = repair_caller_before_callee(["main", "leaf", "orphan"], outgoing)

    assert repaired.index("orphan") < repaired.index("leaf")


def test_orphan_caller_repaired_before_callee():
    nodes = [
        {
            "id": "main",
            "data": {
                "label": "main",
                "file": "repo/main.py",
                "entry_point": True,
                "lineno": 1,
                "loc": 5,
                "public_api": True,
            },
        },
        {
            "id": "leaf",
            "data": {
                "label": "leaf",
                "file": "repo/leaf.py",
                "lineno": 1,
                "loc": 4,
                "public_api": True,
            },
        },
        {
            "id": "orphan",
            "data": {
                "label": "orphan",
                "file": "repo/orphan.py",
                "lineno": 1,
                "loc": 3,
                "public_api": False,
            },
        },
    ]
    edges = [
        {"source": "main", "target": "leaf"},
        {"source": "orphan", "target": "leaf"},
    ]

    steps = build_learning_path(nodes, edges)
    ordered = [step["node_id"] for step in steps]

    assert ordered.index("orphan") < ordered.index("leaf")
    report = assess_learning_path(steps, nodes, edges)
    assert report.caller_before_callee


def test_apply_rebuilds_step_numbers_after_repair():
    nodes = _sample_nodes()
    edges = _sample_edges()
    baseline = build_learning_path(nodes, edges)
    shuffled = [
        baseline[2],
        baseline[0],
        baseline[1],
        baseline[3],
    ]
    for index, step in enumerate(shuffled, start=1):
        step["step"] = index

    repaired = apply_learning_path_quality(shuffled, nodes, edges)

    assert [step["step"] for step in repaired] == [1, 2, 3, 4]
    report = assess_learning_path(repaired, nodes, edges)
    assert report.caller_before_callee


def test_ai_refinement_preserves_call_order_and_custom_reason():
    baseline = build_learning_path(_sample_nodes(), _sample_edges())

    def fake_refiner(window):
        return [
            {"node_id": "load_config", "reason": "Start with configuration."},
            {"node_id": "made_up", "reason": "This must be ignored."},
        ]

    refined = refine_learning_path_with_ai(
        baseline,
        fake_refiner,
        window_size=3,
        nodes=_sample_nodes(),
        edges=_sample_edges(),
    )

    assert [step["node_id"] for step in refined] == [
        "main",
        "load_config",
        "Api.create",
        "_normalize",
    ]
    config_step = next(step for step in refined if step["node_id"] == "load_config")
    assert config_step["reason"] == "Start with configuration."
