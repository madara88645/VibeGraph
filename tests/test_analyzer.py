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

class TestIsLocalModule(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        CodeAnalyzer._is_local_module.cache_clear()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        CodeAnalyzer._is_local_module.cache_clear()

    def test_local_module_py_file(self):
        """Test detection of a plain .py file."""
        module_path = os.path.join(self.tmpdir, "my_module.py")
        with open(module_path, "w", encoding="utf-8") as f:
            f.write("# dummy")

        self.assertTrue(CodeAnalyzer._is_local_module("my_module", self.tmpdir))

    def test_local_module_package(self):
        """Test detection of a package directory with __init__.py."""
        pkg_path = os.path.join(self.tmpdir, "my_package")
        os.makedirs(pkg_path)
        with open(os.path.join(pkg_path, "__init__.py"), "w", encoding="utf-8") as f:
            f.write("# dummy")

        self.assertTrue(CodeAnalyzer._is_local_module("my_package", self.tmpdir))

    def test_nested_local_module(self):
        """Test detection of a nested module inside a package."""
        pkg_path = os.path.join(self.tmpdir, "my_package")
        os.makedirs(pkg_path)
        with open(os.path.join(pkg_path, "__init__.py"), "w", encoding="utf-8") as f:
            f.write("# dummy")
        with open(os.path.join(pkg_path, "nested_module.py"), "w", encoding="utf-8") as f:
            f.write("# dummy")

        self.assertTrue(CodeAnalyzer._is_local_module("my_package.nested_module", self.tmpdir))

    def test_nested_local_package(self):
        """Test detection of a nested package."""
        nested_pkg_path = os.path.join(self.tmpdir, "my_package", "nested_package")
        os.makedirs(nested_pkg_path)
        with open(os.path.join(self.tmpdir, "my_package", "__init__.py"), "w", encoding="utf-8") as f:
            f.write("# dummy")
        with open(os.path.join(nested_pkg_path, "__init__.py"), "w", encoding="utf-8") as f:
            f.write("# dummy")

        self.assertTrue(CodeAnalyzer._is_local_module("my_package.nested_package", self.tmpdir))

    def test_directory_without_init(self):
        """Test that a directory without __init__.py is not considered a local module."""
        dir_path = os.path.join(self.tmpdir, "just_a_dir")
        os.makedirs(dir_path)

        self.assertFalse(CodeAnalyzer._is_local_module("just_a_dir", self.tmpdir))

    def test_nonexistent_module(self):
        """Test that a non-existent module returns False."""
        self.assertFalse(CodeAnalyzer._is_local_module("does_not_exist", self.tmpdir))


if __name__ == "__main__":
    unittest.main()
