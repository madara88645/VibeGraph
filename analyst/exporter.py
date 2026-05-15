import time

import networkx as nx
import json
from typing import Dict, Any


class GraphExporter:
    def __init__(self):
        pass

    def export_to_react_flow(
        self,
        graph: nx.DiGraph,
        output_path: str | None = None,
        dependencies: list[dict] | None = None,
        _profile: dict | None = None,
    ) -> Dict[str, Any]:
        """
        Converts a NetworkX graph to a JSON format suitable for React Flow.

        Parameters
        ----------
        dependencies : list[dict], optional
            Output of ``CodeAnalyzer.extract_dependencies`` for one or more
            files.  Each dict must have ``file`` and ``dependencies`` keys.
        """
        nodes = []
        edges = []

        # Convert nodes
        _t_nodes = time.perf_counter() if _profile is not None else 0.0
        for node_id, data in graph.nodes(data=True):
            # Extract metadata
            node_type = data.get("type", "default")

            # React Flow node structure
            node_dict = {
                "id": node_id,
                "type": "default",  # Use 'input', 'output', or custom types if needed
                "data": {
                    "label": node_id,
                    "type": node_type,  # Include type in data as requested
                    **data,  # Include other metadata like lineno, docstring
                },
                "position": {
                    "x": 0,
                    "y": 0,
                },  # Default position, frontend handles layout
            }
            nodes.append(node_dict)
        if _profile is not None:
            _profile["nodes_build_ms"] = round((time.perf_counter() - _t_nodes) * 1000, 2)

        # Detect cycles
        # Optimization: Use strongly_connected_components O(V+E) instead of simple_cycles O((V+E)C)
        # An edge is part of a cycle if both endpoints belong to the same SCC of size > 1.
        cycle_edges = set()
        _t_scc = time.perf_counter() if _profile is not None else 0.0
        try:
            node_to_component = {}
            for i, component in enumerate(nx.strongly_connected_components(graph)):
                if len(component) > 1:
                    for node in component:
                        node_to_component[node] = i

            for u, v in graph.edges():
                if (
                    u != v
                    and u in node_to_component
                    and v in node_to_component
                    and node_to_component[u] == node_to_component[v]
                ):
                    cycle_edges.add((u, v))
        except nx.NetworkXError:
            pass  # Graph may not support cycle detection
        if _profile is not None:
            _profile["scc_ms"] = round((time.perf_counter() - _t_scc) * 1000, 2)

        # Convert edges
        _t_edges = time.perf_counter() if _profile is not None else 0.0
        for u, v, data in graph.edges(data=True):
            edge_dict = {
                "id": f"e{u}-{v}",
                "source": u,
                "target": v,
                "animated": True,  # Optional visual polish
                "data": {"is_cycle_edge": (u, v) in cycle_edges},
            }
            edges.append(edge_dict)

        output_data = {"nodes": nodes, "edges": edges}
        if _profile is not None:
            _profile["edges_build_ms"] = round((time.perf_counter() - _t_edges) * 1000, 2)
            _profile["export_build_ms"] = round(
                _profile.get("nodes_build_ms", 0.0) + _profile.get("edges_build_ms", 0.0),
                2,
            )
            _profile["export_node_count"] = len(nodes)
            _profile["export_edge_count"] = len(edges)

        # ---- file_dependencies (optional) ----
        if dependencies:
            file_deps = []
            for dep_info in dependencies:
                source_file = dep_info.get("file", "unknown")
                for dep in dep_info.get("dependencies", []):
                    if dep.get("is_local"):
                        file_deps.append(
                            {
                                "source_file": source_file,
                                "target_file": dep["module"],
                                "imports": dep["names"],
                            }
                        )
            output_data["file_dependencies"] = file_deps

        if output_path:
            # Ensure directory exists
            import os

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)

        return output_data
