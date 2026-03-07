import os
import tempfile
import unittest
from analyst.analyzer import CodeAnalyzer

class TestCodeAnalyzerStructure(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.dummy_file = os.path.join(self.tmpdir, "dummy.py")
        self.dummy_code = '''def helper():\n    pass\n\ndef main():\n    helper()\n'''
        with open(self.dummy_file, "w", encoding="utf-8") as f:
            f.write(self.dummy_code)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_analyze_structure_success(self):
        analyzer = CodeAnalyzer()
        summary = analyzer.analyze_structure(self.dummy_file)

        # Determine exactly what the graph will have.
        # Nodes: helper, main. Edge: main -> helper.
        # Actually NetworkX nodes/edges are just node names.

        # We need to consider node iteration order, so we shouldn't strictly match the whole string
        # unless we know the order. NetworkX preserves insertion order.
        # CallGraphVisitor visits definitions: helper then main.
        # Let's verify each part explicitly to avoid flakiness over ordering.

        self.assertTrue(summary.startswith(f"Target: {self.dummy_file}\n"))
        self.assertIn("Nodes (2):", summary)
        self.assertIn("helper", summary)
        self.assertIn("main", summary)
        self.assertIn("Edges (1):", summary)
        self.assertIn("('main', 'helper')", summary)

        # A full exact string check if we expect stable ordering
        # If order is stable, we can do an exact match:
        result = analyzer.analyze_file(self.dummy_file)
        graph = result["graph"]
        exact_expected = f"Target: {self.dummy_file}\nNodes ({graph.number_of_nodes()}): {', '.join(graph.nodes())}\nEdges ({graph.number_of_edges()}): {list(graph.edges())}\n"
        self.assertEqual(summary, exact_expected)

    def test_analyze_structure_error(self):
        analyzer = CodeAnalyzer()
        non_existent_file = os.path.join(self.tmpdir, "nonexistent.py")
        summary = analyzer.analyze_structure(non_existent_file)
        self.assertEqual(summary, f"Path not found: {non_existent_file}")

if __name__ == "__main__":
    unittest.main()
