"""Tests for deterministic repo-wide learning path generation."""

from app.services.learning_path import (
    build_learning_path,
    refine_learning_path_with_ai,
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


def test_fixed_sample_graph_returns_stable_order_starting_at_entry_point():
    steps = build_learning_path(_sample_nodes(), _sample_edges())

    assert [step["node_id"] for step in steps] == [
        "main",
        "Api.create",
        "load_config",
        "_normalize",
    ]
    assert steps[0]["signals"]["entry_point"] is True
    assert steps[0]["node_id"] in {node["id"] for node in _sample_nodes()}


def test_private_internal_nodes_rank_after_public_api_nodes():
    steps = build_learning_path(_sample_nodes(), _sample_edges())
    ordered_ids = [step["node_id"] for step in steps]

    assert ordered_ids.index("_normalize") > ordered_ids.index("Api.create")


def test_side_effect_boundary_gets_signal_and_reason():
    steps = build_learning_path(_sample_nodes(), _sample_edges())
    config_step = next(step for step in steps if step["node_id"] == "load_config")

    assert config_step["signals"]["side_effect_boundary"] is True
    assert "side effects" in config_step["reason"].lower()


def test_ai_refinement_discards_hallucinated_nodes_and_preserves_missing_baseline():
    baseline = build_learning_path(_sample_nodes(), _sample_edges())

    def fake_refiner(window):
        return [
            {"node_id": "load_config", "reason": "Start with configuration."},
            {"node_id": "made_up", "reason": "This must be ignored."},
        ]

    refined = refine_learning_path_with_ai(baseline, fake_refiner, window_size=3)

    assert [step["node_id"] for step in refined] == [
        "load_config",
        "main",
        "Api.create",
        "_normalize",
    ]
    assert all(
        step["node_id"] in {node["id"] for node in _sample_nodes()} for step in refined
    )
    assert [step["step"] for step in refined] == [1, 2, 3, 4]
