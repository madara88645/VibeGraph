import networkx as nx


class BasicTeacher:
    def generate_lesson(self, graph: nx.DiGraph, file_path: str) -> str:
        """Generates a lesson summary based on the graph structure."""
        if not isinstance(graph, nx.DiGraph):
            raise ValueError("Invalid graph provided")

        lesson_parts = [f"# Lesson: Understanding {file_path}\n\n"]

        # 1. Structure Overview
        lesson_parts.append("## 1. Structural Overview\n")
        classes = [n for n, d in graph.nodes(data=True) if d.get("type") == "class"]
        functions = [
            n for n, d in graph.nodes(data=True) if d.get("type") == "function"
        ]

        if classes:
            class_word = "class" if len(classes) == 1 else "classes"
            lesson_parts.append(
                f"This module contains **{len(classes)} {class_word}**: `{', '.join(classes)}`.\n"
            )
        if functions:
            lesson_parts.append(
                f"It defines **{len(functions)} functions**: `{', '.join(functions)}`.\n"
            )

        # 2. Key Interactions (Edges)
        lesson_parts.append("\n## 2. Key Interactions\n")
        if graph.number_of_edges() > 0:
            lesson_parts.append("Here is how the components interact:\n")
            edges_text = [f"- `{u}` calls `{v}`\n" for u, v in graph.edges()]
            lesson_parts.append("".join(edges_text))
        else:
            lesson_parts.append("No internal function calls detected in this file.\n")

        # 3. Complexity Hint
        density = nx.density(graph)
        lesson_parts.append("\n## 3. Analysis\n")
        if density > 0.5:
            lesson_parts.append(
                "This module is **highly coupled** (many connections).\n"
            )
        else:
            lesson_parts.append(
                "This module is **loosely coupled** (few connections).\n"
            )

        return "".join(lesson_parts)
