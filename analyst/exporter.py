"""Graph exporter — converts a CallGraph to React Flow JSON.

Output schema:
{
  "nodes": [
    {
      "id": "<node_id>",
      "type": "custom",
      "data": {
        "label": "<label>",
        "nodeType": "function"|"class"|"entry",
        "file": "<relative_file_path>",
        "lineno": <int>,
        "source": "<source_code>"
      },
      "position": { "x": 0, "y": 0 }
    },
    ...
  ],
  "edges": [
    {
      "id": "<source>-><target>",
      "source": "<source_id>",
      "target": "<target_id>",
      "data": { "crossFile": true|false }
    },
    ...
  ]
}

Positions are left as (0, 0) — the React frontend applies dagre layout.
"""

import json
from pathlib import Path
from typing import Optional

from analyst.analyzer import CallGraph


def graph_to_dict(graph: CallGraph) -> dict:
    """Convert a CallGraph to the React Flow JSON dict."""
    nodes = []
    for node in graph.nodes.values():
        nodes.append({
            "id": node.id,
            "type": "custom",
            "data": {
                "label": node.label,
                "nodeType": node.node_type,
                "file": node.file,
                "lineno": node.lineno,
                "source": node.source,
            },
            "position": {"x": 0, "y": 0},
        })

    edges = []
    for edge in graph.edges:
        edges.append({
            "id": f"{edge.source}->{edge.target}",
            "source": edge.source,
            "target": edge.target,
            "data": {"crossFile": edge.cross_file},
        })

    return {"nodes": nodes, "edges": edges}


def export_graph(
    graph: Optional[CallGraph] = None,
    output_path: str = "explorer/public/graph_data.json",
) -> None:
    """Serialize *graph* to JSON and write to *output_path*.

    If *graph* is None, writes an empty graph so the frontend still loads.
    """
    if graph is None:
        data = {"nodes": [], "edges": []}
    else:
        data = graph_to_dict(graph)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
