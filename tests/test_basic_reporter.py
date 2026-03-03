import unittest
import networkx as nx

from teacher.basic_reporter import BasicTeacher

class TestBasicTeacher(unittest.TestCase):
    def setUp(self):
        self.teacher = BasicTeacher()

    def test_empty_graph(self):
        graph = nx.DiGraph()
        lesson = self.teacher.generate_lesson(graph, "empty.py")

        self.assertIn("# Lesson: Understanding empty.py", lesson)
        self.assertIn("No internal function calls detected in this file.", lesson)
        self.assertIn("This module is **loosely coupled**", lesson)
        self.assertNotIn("This module contains", lesson)
        self.assertNotIn("It defines", lesson)

    def test_only_classes(self):
        graph = nx.DiGraph()
        graph.add_node("MyClass", type="class")
        graph.add_node("OtherClass", type="class")

        lesson = self.teacher.generate_lesson(graph, "classes.py")

        self.assertIn("This module contains **2 classes**: `MyClass, OtherClass`.", lesson)
        self.assertNotIn("It defines", lesson)
        self.assertIn("No internal function calls detected in this file.", lesson)
        self.assertIn("This module is **loosely coupled**", lesson)

    def test_only_functions(self):
        graph = nx.DiGraph()
        graph.add_node("my_func", type="function")
        graph.add_node("other_func", type="function")

        lesson = self.teacher.generate_lesson(graph, "functions.py")

        self.assertNotIn("This module contains", lesson)
        self.assertIn("It defines **2 functions**: `my_func, other_func`.", lesson)
        self.assertIn("No internal function calls detected in this file.", lesson)
        self.assertIn("This module is **loosely coupled**", lesson)

    def test_mixed_with_edges(self):
        graph = nx.DiGraph()
        graph.add_node("MyClass", type="class")
        graph.add_node("my_func", type="function")
        graph.add_node("helper_func", type="function")

        graph.add_edge("my_func", "helper_func")
        graph.add_edge("MyClass", "my_func")

        lesson = self.teacher.generate_lesson(graph, "mixed.py")

        self.assertIn("This module contains **1 classes**: `MyClass`.", lesson)
        self.assertIn("It defines **2 functions**: `my_func, helper_func`.", lesson)
        self.assertIn("Here is how the components interact:", lesson)
        self.assertIn("- `my_func` calls `helper_func`", lesson)
        self.assertIn("- `MyClass` calls `my_func`", lesson)

    def test_high_coupling(self):
        graph = nx.DiGraph()
        # To get density > 0.5 we need more than half the possible edges
        # For 3 nodes, max edges = 3 * 2 = 6. Density > 0.5 means > 3 edges. Let's add 4.
        nodes = ["A", "B", "C"]
        for n in nodes:
            graph.add_node(n, type="function")

        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "A")
        graph.add_edge("A", "C")

        # Density calculation: E / (V*(V-1)) = 4 / (3*2) = 4/6 = 0.66 > 0.5

        lesson = self.teacher.generate_lesson(graph, "coupled.py")
        self.assertIn("This module is **highly coupled** (many connections).", lesson)

if __name__ == "__main__":
    unittest.main()
