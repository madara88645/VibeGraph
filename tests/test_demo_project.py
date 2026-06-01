import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import create_app
from app.utils.security import is_safe_path
from app.utils.snippet import extract_snippet


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_GRAPH_PATH = REPO_ROOT / "explorer" / "public" / "demo_graph_data.json"
DEMO_SOURCE_ROOT = REPO_ROOT / "app" / "demo_project"
client = TestClient(create_app(), raise_server_exceptions=False)


def _load_demo_graph():
    with DEMO_GRAPH_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def test_demo_graph_is_small_enough_for_first_run():
    graph = _load_demo_graph()

    assert len(graph["nodes"]) <= 80
    assert len(graph["edges"]) <= 180
    assert graph.get("meta", {}).get("truncated") is False


def test_demo_graph_showcases_core_node_shapes_and_languages():
    graph = _load_demo_graph()
    node_data = [node["data"] for node in graph["nodes"]]
    node_types = {data.get("type") for data in node_data}
    languages = {data.get("language") for data in node_data}

    assert {"module", "class", "function"}.issubset(node_types)
    assert "python" in languages
    assert "javascript" in languages
    assert "typescript" in languages
    assert node_types.intersection({"builtin", "external", "unresolved"})


def test_demo_graph_source_files_are_bundled_and_safe_for_code_panel():
    graph = _load_demo_graph()
    source_files = {
        node["data"].get("file")
        for node in graph["nodes"]
        if node["data"].get("file")
        and node["data"].get("type") not in {"builtin", "external", "unresolved"}
    }

    assert source_files
    for file_path in source_files:
        assert file_path.startswith("app/demo_project/")
        assert (REPO_ROOT / file_path).exists()
        assert is_safe_path(file_path) is True


def test_demo_project_js_snippet_is_available_to_code_panel():
    snippet, start_line, end_line, full_source = extract_snippet(
        "app/demo_project/web.js",
        "bootDashboard",
        language="javascript",
        start_line=17,
        end_line=23,
    )

    assert "export async function bootDashboard" in snippet
    assert "client.fetchPlan" in snippet
    assert start_line == 17
    assert end_line == 23
    assert full_source and "class DemoClient" in full_source


def test_demo_project_snippet_endpoint_returns_source_for_code_panel_payload():
    response = client.post(
        "/api/snippet",
        json={
            "file_path": "app/demo_project/web.js",
            "node_id": "bootDashboard",
            "language": "javascript",
            "start_line": 17,
            "end_line": 23,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "export async function bootDashboard" in data["snippet"]
    assert data["start_line"] == 17
    assert data["end_line"] == 23
    assert data["language"] == "javascript"
