"""Unit tests for the improved deterministic Learning Path logic."""

import pytest
from app.services.learning_path import build_learning_path, refine_learning_path_with_ai


def test_stable_output_for_fixed_sample_graph():
    """Verify that build_learning_path produces perfectly stable, deterministic output for a fixed graph."""
    nodes = [
        {
            "id": "server",
            "data": {
                "label": "serve.py",
                "file": "serve.py",
                "entry_point": True,
                "loc": 50,
            },
        },
        {
            "id": "router",
            "data": {
                "label": "router.py",
                "file": "app/router.py",
                "api_boundary": True,
                "loc": 80,
            },
        },
        {
            "id": "db",
            "data": {
                "label": "db.py",
                "file": "app/db.py",
                "side_effect_boundary": True,
                "loc": 40,
            },
        },
        {
            "id": "utils",
            "data": {
                "label": "utils.py",
                "file": "app/utils.py",
                "loc": 20,
            },
        },
    ]
    edges = [
        {"source": "server", "target": "router"},
        {"source": "router", "target": "db"},
        {"source": "db", "target": "utils"},
    ]

    # Run multiple times to verify absolute determinism
    first_run = build_learning_path(nodes, edges)
    for _ in range(5):
        run = build_learning_path(nodes, edges)
        assert [step["node_id"] for step in run] == [step["node_id"] for step in first_run]
        assert [step["score"] for step in run] == [step["score"] for step in first_run]


def test_path_starts_from_real_entry_point():
    """Verify that the generated path prioritizes real entry points and works down dependencies."""
    nodes = [
        {
            "id": "helper",
            "data": {
                "label": "helper",
                "file": "helper.py",
                "loc": 10,
            },
        },
        {
            "id": "entry",
            "data": {
                "label": "main",
                "file": "main.py",
                "entry_point": True,
                "loc": 30,
            },
        },
        {
            "id": "core",
            "data": {
                "label": "core",
                "file": "core.py",
                "loc": 150,  # High complexity penalty
            },
        },
    ]
    edges = [
        {"source": "entry", "target": "core"},
        {"source": "core", "target": "helper"},
    ]

    path = build_learning_path(nodes, edges)
    node_ids = [step["node_id"] for step in path]

    # The entry point must be the first item in the learning path
    assert node_ids[0] == "entry"
    assert "core" in node_ids
    assert "helper" in node_ids


def test_no_hallucinated_nodes_and_safe_fallback_in_refinement():
    """Verify that refine_learning_path_with_ai filters hallucinated nodes and restores forgotten nodes."""
    baseline_steps = [
        {"node_id": "main", "node_name": "main", "file_path": "main.py", "reason": "Starts here"},
        {"node_id": "auth", "node_name": "auth", "file_path": "auth.py", "reason": "Handles auth"},
        {"node_id": "db", "node_name": "db", "file_path": "db.py", "reason": "Saves state"},
        {"node_id": "util", "node_name": "util", "file_path": "util.py", "reason": "Helpers"},
    ]

    def faulty_ai_refiner(window):
        # AI returns an invented/hallucinated node and forgets "util"
        return [
            {"node_id": "db", "reason": "Refined DB reason"},
            {"node_id": "hallucinated_fake_node", "reason": "Invented node"},
            {"node_id": "auth", "reason": "Refined Auth reason"},
            {"node_id": "main", "reason": "Refined Main reason"},
        ]

    refined = refine_learning_path_with_ai(baseline_steps, faulty_ai_refiner, window_size=4)
    refined_ids = [step["node_id"] for step in refined]

    # 1. Hallucinated nodes must be strictly removed
    assert "hallucinated_fake_node" not in refined_ids

    # 2. Every single original node must be preserved (none lost, "util" restored to the end of the window)
    assert set(refined_ids) == {"main", "auth", "db", "util"}
    assert refined_ids[-1] == "util"  # Forgotten nodes fall back gracefully to the end of the window

    # 3. Step numbers are correctly reset to 1-indexed sequential integers
    assert [step["step"] for step in refined] == [1, 2, 3, 4]


def test_disjoint_subgraphs_traversal():
    """Verify that multiple unconnected components are fully walked in logical entry sequence."""
    nodes = [
        # Subgraph A: Server
        {
            "id": "server",
            "data": {
                "label": "serve.py",
                "file": "serve.py",
                "entry_point": True,
            },
        },
        {
            "id": "server_helper",
            "data": {
                "label": "server_helper",
                "file": "server_helper.py",
            },
        },
        # Subgraph B: CLI Tools
        {
            "id": "cli",
            "data": {
                "label": "cli.py",
                "file": "cli.py",
                "entry_point": True,
            },
        },
        {
            "id": "cli_helper",
            "data": {
                "label": "cli_helper",
                "file": "cli_helper.py",
            },
        },
    ]
    edges = [
        {"source": "server", "target": "server_helper"},
        {"source": "cli", "target": "cli_helper"},
    ]

    path = build_learning_path(nodes, edges)
    node_ids = [step["node_id"] for step in path]

    # All nodes must be present
    assert len(node_ids) == 4
    assert set(node_ids) == {"server", "server_helper", "cli", "cli_helper"}

    # Both entry points should come before their helpers
    assert node_ids.index("server") < node_ids.index("server_helper")
    assert node_ids.index("cli") < node_ids.index("cli_helper")
