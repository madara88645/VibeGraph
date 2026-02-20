"""Offline markdown report generator.

Produces a human-readable Markdown summary of the call graph without
requiring a network connection or API key.
"""

from typing import Dict, List


class BasicReporter:
    """Generates a Markdown report from React Flow graph data (dict)."""

    def __init__(self, graph_data: dict):
        self.nodes: List[dict] = graph_data.get("nodes", [])
        self.edges: List[dict] = graph_data.get("edges", [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> str:
        sections = [
            "# VibeGraph — Code Analysis Report\n",
            self._summary_section(),
            self._nodes_by_file_section(),
            self._edges_section(),
        ]
        return "\n".join(sections)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _summary_section(self) -> str:
        num_nodes = len(self.nodes)
        num_edges = len(self.edges)
        files = {n["data"]["file"] for n in self.nodes}
        return (
            f"## Summary\n\n"
            f"| Metric | Count |\n"
            f"|--------|-------|\n"
            f"| Files analyzed | {len(files)} |\n"
            f"| Nodes (functions + classes + entries) | {num_nodes} |\n"
            f"| Call edges | {num_edges} |\n"
        )

    def _nodes_by_file_section(self) -> str:
        by_file: Dict[str, List[dict]] = {}
        for node in self.nodes:
            f = node["data"]["file"]
            by_file.setdefault(f, []).append(node)

        lines = ["## Nodes by File\n"]
        for file_path, nodes in sorted(by_file.items()):
            lines.append(f"### `{file_path}`\n")
            for node in sorted(nodes, key=lambda n: n["data"]["lineno"]):
                icon = {"function": "⚡", "class": "🏗️", "entry": "🚀"}.get(
                    node["data"]["nodeType"], "•"
                )
                lines.append(
                    f"- {icon} **{node['data']['label']}** (line {node['data']['lineno']})"
                )
            lines.append("")

        return "\n".join(lines)

    def _edges_section(self) -> str:
        if not self.edges:
            return "## Call Edges\n\n*No call relationships found.*\n"

        id_to_label = {n["id"]: n["data"]["label"] for n in self.nodes}

        lines = ["## Call Edges\n"]
        for edge in self.edges:
            src_label = id_to_label.get(edge["source"], edge["source"])
            tgt_label = id_to_label.get(edge["target"], edge["target"])
            cross = " *(cross-file)*" if edge.get("data", {}).get("crossFile") else ""
            lines.append(f"- `{src_label}` → `{tgt_label}`{cross}")

        lines.append("")
        return "\n".join(lines)
