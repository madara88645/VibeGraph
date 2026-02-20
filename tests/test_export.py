"""Tests for analyst.exporter — graph → React Flow JSON conversion."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from analyst.analyzer import CallGraph, NodeInfo, EdgeInfo
from analyst.exporter import graph_to_dict, export_graph


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_graph() -> CallGraph:
    g = CallGraph()
    g.nodes["a.py::foo"] = NodeInfo(
        id="a.py::foo",
        label="foo",
        node_type="function",
        file="a.py",
        lineno=1,
        source="def foo(): pass",
    )
    g.nodes["a.py::Bar"] = NodeInfo(
        id="a.py::Bar",
        label="Bar",
        node_type="class",
        file="a.py",
        lineno=5,
        source="class Bar: pass",
    )
    g.nodes["b.py::__main__"] = NodeInfo(
        id="b.py::__main__",
        label="__main__",
        node_type="entry",
        file="b.py",
        lineno=10,
        source='if __name__ == "__main__": foo()',
    )
    g.edges.append(EdgeInfo(source="b.py::__main__", target="a.py::foo", cross_file=True))
    return g


# ---------------------------------------------------------------------------
# graph_to_dict
# ---------------------------------------------------------------------------

class TestGraphToDict:
    def test_node_count(self):
        data = graph_to_dict(_make_graph())
        assert len(data["nodes"]) == 3

    def test_edge_count(self):
        data = graph_to_dict(_make_graph())
        assert len(data["edges"]) == 1

    def test_node_shape(self):
        data = graph_to_dict(_make_graph())
        node = next(n for n in data["nodes"] if n["id"] == "a.py::foo")
        assert node["type"] == "custom"
        assert node["data"]["label"] == "foo"
        assert node["data"]["nodeType"] == "function"
        assert node["data"]["file"] == "a.py"
        assert node["data"]["lineno"] == 1
        assert "source" in node["data"]
        assert "position" in node
        assert node["position"] == {"x": 0, "y": 0}

    def test_class_node_type(self):
        data = graph_to_dict(_make_graph())
        bar = next(n for n in data["nodes"] if n["id"] == "a.py::Bar")
        assert bar["data"]["nodeType"] == "class"

    def test_entry_node_type(self):
        data = graph_to_dict(_make_graph())
        entry = next(n for n in data["nodes"] if n["id"] == "b.py::__main__")
        assert entry["data"]["nodeType"] == "entry"

    def test_edge_shape(self):
        data = graph_to_dict(_make_graph())
        edge = data["edges"][0]
        assert edge["source"] == "b.py::__main__"
        assert edge["target"] == "a.py::foo"
        assert edge["data"]["crossFile"] is True
        assert edge["id"] == "b.py::__main__->a.py::foo"

    def test_empty_graph(self):
        data = graph_to_dict(CallGraph())
        assert data == {"nodes": [], "edges": []}

    def test_serializable(self):
        data = graph_to_dict(_make_graph())
        # Should not raise
        json.dumps(data)


# ---------------------------------------------------------------------------
# export_graph
# ---------------------------------------------------------------------------

class TestExportGraph:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "graph_data.json"
        export_graph(_make_graph(), output_path=str(out))
        assert out.exists()

    def test_valid_json(self, tmp_path):
        out = tmp_path / "graph_data.json"
        export_graph(_make_graph(), output_path=str(out))
        data = json.loads(out.read_text())
        assert "nodes" in data
        assert "edges" in data

    def test_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b" / "graph.json"
        export_graph(_make_graph(), output_path=str(nested))
        assert nested.exists()

    def test_none_graph_writes_empty(self, tmp_path):
        out = tmp_path / "graph_data.json"
        export_graph(None, output_path=str(out))
        data = json.loads(out.read_text())
        assert data == {"nodes": [], "edges": []}

    def test_node_data_in_file(self, tmp_path):
        out = tmp_path / "graph_data.json"
        export_graph(_make_graph(), output_path=str(out))
        data = json.loads(out.read_text())
        labels = {n["data"]["label"] for n in data["nodes"]}
        assert labels == {"foo", "Bar", "__main__"}
