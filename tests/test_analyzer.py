import unittest
import os
import shutil
import tempfile
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst.analyzer import CodeAnalyzer, MAX_FILE_SIZE


class TestCodeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.analyzer = CodeAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content):
        full_path = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    def test_analyze_single_file_basic(self):
        code = """
def hello():
    print("world")

class MyClass:
    def __init__(self):
        pass
"""
        file_path = self.create_file("basic.py", code)
        result = self.analyzer.analyze_file(file_path)

        self.assertIn("file", result)
        self.assertEqual(result["file"], file_path)
        self.assertIn("definitions", result)

        def_names = [d["name"] for d in result["definitions"]]
        self.assertIn("hello", def_names)
        self.assertIn("MyClass", def_names)
        self.assertIn("MyClass.__init__", def_names)

        graph = result["graph"]
        self.assertTrue(graph.has_node("hello"))
        self.assertTrue(graph.has_node("MyClass"))
        self.assertTrue(graph.has_node("MyClass.__init__"))

    def test_analyze_single_file_with_calls(self):
        code = """
def func_a():
    func_b()

def func_b():
    pass

class MyClass:
    def method_a(self):
        self.method_b()

    def method_b(self):
        func_a()
"""
        file_path = self.create_file("calls.py", code)
        result = self.analyzer.analyze_file(file_path)
        graph = result["graph"]

        self.assertTrue(graph.has_edge("func_a", "func_b"))
        self.assertTrue(graph.has_edge("MyClass.method_a", "method_b"))
        self.assertTrue(graph.has_edge("MyClass.method_b", "func_a"))

    def test_analyze_directory(self):
        self.create_file("pkg1/a.py", "def a(): pass")
        self.create_file("pkg1/b.py", "from pkg1.a import a\ndef b(): a()")
        self.create_file("pkg2/c.py", "def c(): pass")

        result = self.analyzer.analyze_file(self.test_dir)

        self.assertEqual(result["file"], self.test_dir)
        def_names = [d["name"] for d in result["definitions"]]
        self.assertIn("a", def_names)
        self.assertIn("b", def_names)
        self.assertIn("c", def_names)

        graph = result["graph"]
        self.assertTrue(graph.has_node("a"))
        self.assertTrue(graph.has_node("b"))
        self.assertTrue(graph.has_node("c"))
        self.assertTrue(graph.has_edge("b", "a"))

    def test_ignored_dirs(self):
        self.create_file(".git/config", "some config")
        self.create_file(".git/hooks/pre-commit", "echo 1")
        self.create_file("node_modules/pkg/index.py", "def node_func(): pass")
        self.create_file("valid.py", "def valid_func(): pass")

        result = self.analyzer.analyze_file(self.test_dir)
        def_names = [d["name"] for d in result["definitions"]]

        self.assertIn("valid_func", def_names)
        self.assertNotIn("node_func", def_names)

    def test_file_too_large(self):
        file_path = self.create_file("large.py", " " * (MAX_FILE_SIZE + 1))
        result = self.analyzer.analyze_file(file_path)

        self.assertIn("error", result)
        self.assertIn("exceeds maximum allowed size", result["error"])

    def test_syntax_error(self):
        file_path = self.create_file("bad.py", "def incomplete(")
        result = self.analyzer.analyze_file(file_path)

        self.assertIn("error", result)
        self.assertIn("Syntax error", result["error"])

    def test_path_not_found(self):
        result = self.analyzer.analyze_file("/non/existent/path")
        self.assertIn("error", result)
        self.assertIn("Path not found", result["error"])

    def test_extract_dependencies(self):
        code = """
import os
import sys as system
from networkx import DiGraph
from .local_mod import local_func
from app.utils import something
import unknown_mod

def main():
    pass
"""
        file_path = self.create_file("main.py", code)
        self.create_file("local_mod.py", "def local_func(): pass")
        self.create_file("app/__init__.py", "")
        self.create_file("app/utils.py", "def something(): pass")

        result = self.analyzer.extract_dependencies(
            file_path, project_root=self.test_dir
        )
        deps = result["dependencies"]

        # os
        os_dep = next(d for d in deps if d["module"] == "os")
        self.assertFalse(os_dep["is_local"])

        # sys as system
        sys_dep = next(d for d in deps if d["module"] == "sys")
        self.assertIn("system", sys_dep["names"])
        self.assertFalse(sys_dep["is_local"])

        # networkx
        nx_dep = next(d for d in deps if d["module"] == "networkx")
        self.assertFalse(nx_dep["is_local"])

        # .local_mod (relative)
        local_dep = next(d for d in deps if d["module"] == "local_mod")
        self.assertTrue(local_dep["is_local"])

        # app.utils
        app_dep = next(d for d in deps if d["module"] == "app.utils")
        self.assertTrue(app_dep["is_local"])

        # unknown_mod
        unknown_dep = next(d for d in deps if d["module"] == "unknown_mod")
        self.assertFalse(unknown_dep["is_local"])

    def test_extract_dependencies_file_not_found(self):
        result = self.analyzer.extract_dependencies("/non/existent/file.py")
        self.assertIn("error", result)

    def test_extract_dependencies_syntax_error(self):
        file_path = self.create_file("bad_deps.py", "import")
        result = self.analyzer.extract_dependencies(file_path)
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
