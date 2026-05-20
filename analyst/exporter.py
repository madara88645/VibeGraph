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
        max_nodes: int | None = None,
    ) -> Dict[str, Any]:
        """
        Converts a NetworkX graph to a JSON format suitable for React Flow.

        Parameters
        ----------
        dependencies : list[dict], optional
            Output of ``CodeAnalyzer.extract_dependencies`` for one or more
            files.  Each dict must have ``file`` and ``dependencies`` keys.
        max_nodes : int, optional
            Upper bound on emitted nodes. When the graph exceeds this budget,
            nodes are ranked by combined in/out-degree (descending, with node-id
            tiebreak for determinism) and only the top ``max_nodes`` are kept.
            Edges with an endpoint in the elided set are dropped. The result
            includes a ``meta`` block describing what was kept.
        """
        total_v = graph.number_of_nodes()
        total_e = graph.number_of_edges()

        if max_nodes is not None and total_v > max_nodes:
            ranked = sorted(
                graph.nodes(),
                key=lambda n: (-(graph.in_degree(n) + graph.out_degree(n)), str(n)),
            )
            kept: set | None = set(ranked[:max_nodes])
            truncated = True
            # Compute SCCs on the filtered subgraph so cycle flags only reflect
            # edges that will actually be emitted.
            scc_graph = graph.subgraph(kept)
        else:
            kept = None
            truncated = False
            scc_graph = graph

        nodes = []
        edges = []

        # Convert nodes
        _t_nodes = time.perf_counter() if _profile is not None else 0.0
        for node_id, data in graph.nodes(data=True):
            if kept is not None and node_id not in kept:
                continue
            node_type = data.get("type", "default")
            node_dict = {
                "id": node_id,
                "type": "default",
                "data": {
                    "label": node_id,
                    "type": node_type,
                    **data,
                },
                "position": {"x": 0, "y": 0},
            }
            nodes.append(node_dict)
        if _profile is not None:
            _profile["nodes_build_ms"] = round(
                (time.perf_counter() - _t_nodes) * 1000, 2
            )

        # Detect cycles via SCCs on the (possibly filtered) graph.
        cycle_edges = set()
        _t_scc = time.perf_counter() if _profile is not None else 0.0
        try:
            node_to_component = {}
            for i, component in enumerate(nx.strongly_connected_components(scc_graph)):
                if len(component) > 1:
                    for node in component:
                        node_to_component[node] = i

            for u, v in scc_graph.edges():
                if (
                    u != v
                    and u in node_to_component
                    and v in node_to_component
                    and node_to_component[u] == node_to_component[v]
                ):
                    cycle_edges.add((u, v))
        except nx.NetworkXError:
            pass
        if _profile is not None:
            _profile["scc_ms"] = round((time.perf_counter() - _t_scc) * 1000, 2)

        # Convert edges
        _t_edges = time.perf_counter() if _profile is not None else 0.0
        for u, v, data in graph.edges(data=True):
            if kept is not None and (u not in kept or v not in kept):
                continue
            edge_dict = {
                "id": f"e{u}-{v}",
                "source": u,
                "target": v,
                "animated": True,
                "data": {"is_cycle_edge": (u, v) in cycle_edges},
            }
            edges.append(edge_dict)

        output_data: Dict[str, Any] = {"nodes": nodes, "edges": edges}
        output_data["meta"] = {
            "truncated": truncated,
            "total_nodes": total_v,
            "total_edges": total_e,
            "kept_nodes": len(nodes),
            "kept_edges": len(edges),
            "budget": max_nodes,
        }
        if _profile is not None:
            _profile["edges_build_ms"] = round(
                (time.perf_counter() - _t_edges) * 1000, 2
            )
            _profile["export_build_ms"] = round(
                _profile.get("nodes_build_ms", 0.0)
                + _profile.get("edges_build_ms", 0.0),
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
            import os

            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)

        return output_data
