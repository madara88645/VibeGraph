import networkx as nx
import json
from typing import Dict, Any, List

class GraphExporter:
    def __init__(self):
        pass

    def export_to_react_flow(self, graph: nx.DiGraph, output_path: str = None) -> Dict[str, Any]:
        """
        Converts a NetworkX graph to a JSON format suitable for React Flow.
        """
        nodes = []
        edges = []

        # Convert nodes
        for node_id, data in graph.nodes(data=True):
            # Extract metadata
            node_type = data.get("type", "default")
            
            # React Flow node structure
            node_dict = {
                "id": node_id,
                "type": "default",  # Use 'input', 'output', or custom types if needed
                "data": {
                    "label": node_id,
                    "type": node_type, # Include type in data as requested
                    **data # Include other metadata like lineno, docstring
                },
                "position": {"x": 0, "y": 0} # Default position, frontend handles layout
            }
            nodes.append(node_dict)

        # Convert edges
        for u, v, data in graph.edges(data=True):
            edge_dict = {
                "id": f"e{u}-{v}",
                "source": u,
                "target": v,
                "animated": True, # Optional visual polish
            }
            edges.append(edge_dict)

        output_data = {
            "nodes": nodes,
            "edges": edges
        }

        if output_path:
            # Ensure directory exists
            import os
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
        
        return output_data
