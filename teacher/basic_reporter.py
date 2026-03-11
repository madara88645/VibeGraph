import networkx as nx

class BasicTeacher:
    def __init__(self):
        pass

    def generate_lesson(self, graph: nx.DiGraph, file_path: str) -> str:
        """
        Generates a mock 'lesson' based on the graph structure.
        In Phase 3, this will use an LLM.
        """
        if not isinstance(graph, nx.DiGraph):
            raise ValueError("Invalid graph provided")
        
        lesson = f"# Lesson: Understanding {file_path}\n\n"
        
        # 1. Structure Overview
        lesson += "## 1. Structural Overview\n"
        classes = [n for n, d in graph.nodes(data=True) if d.get('type') == 'class']
        functions = [n for n, d in graph.nodes(data=True) if d.get('type') == 'function']
        
        if classes:
            lesson += f"This module contains **{len(classes)} classes**: `{', '.join(classes)}`.\n"
        if functions:
            lesson += f"It defines **{len(functions)} functions**: `{', '.join(functions)}`.\n"
            
        # 2. Key Interactions (Edges)
        lesson += "\n## 2. Key Interactions\n"
        if graph.number_of_edges() > 0:
            lesson += "Here is how the components interact:\n"
            edges_text = [f"- `{u}` calls `{v}`\n" for u, v in graph.edges()]
            lesson += "".join(edges_text)
        else:
            lesson += "No internal function calls detected in this file.\n"

        # 3. Complexity Hint
        density = nx.density(graph)
        lesson += "\n## 3. Analysis\n"
        if density > 0.5:
            lesson += "This module is **highly coupled** (many connections).\n"
        else:
            lesson += "This module is **loosely coupled** (few connections).\n"

        return lesson
