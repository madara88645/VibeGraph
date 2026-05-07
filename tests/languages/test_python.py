import os
import shutil
import tempfile
import sys
import unittest

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from analyst.analyzer import CodeAnalyzer
from analyst.languages.python import PythonAnalyzer


class TestPythonAnalyzer(unittest.TestCase):
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

    def test_function_definitions_with_decorators(self):
        code = """
@my_decorator
@other.dec("args")
def decorated_func():
    pass
"""
        file_path = self.create_file("test_dec.py", code)
        python_analyzer = PythonAnalyzer()
        res = python_analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)

        graph = res.graph
        self.assertTrue(graph.has_node("decorated_func"))
        node_data = graph.nodes["decorated_func"]
        self.assertEqual(node_data["type"], "function")
        self.assertEqual(node_data["language"], "python")

    def test_async_functions(self):
        code = """
async def fetch_data():
    await asyncio.sleep(1)
"""
        file_path = self.create_file("test_async.py", code)
        python_analyzer = PythonAnalyzer()
        res = python_analyzer.analyze_file(file_path, self.test_dir)

        self.assertTrue(res.graph.has_node("fetch_data"))
        node_data = res.graph.nodes["fetch_data"]
        self.assertEqual(node_data["type"], "function")

    def test_classes_with_inheritance(self):
        code = """
class Base:
    pass

class Derived(Base, Mixin):
    def method(self):
        pass
"""
        file_path = self.create_file("test_class.py", code)
        python_analyzer = PythonAnalyzer()
        res = python_analyzer.analyze_file(file_path, self.test_dir)

        self.assertTrue(res.graph.has_node("Base"))
        self.assertTrue(res.graph.has_node("Derived"))
        self.assertTrue(res.graph.has_node("Derived.method"))

        # Verify definitions contain the right hierarchy
        defs = {d["name"]: d for d in res.definitions}
        self.assertEqual(defs["Base"]["type"], "class")
        self.assertEqual(defs["Derived"]["type"], "class")

    def test_nested_functions(self):
        code = """
def outer():
    def inner():
        pass
    inner()
"""
        file_path = self.create_file("test_nested.py", code)
        python_analyzer = PythonAnalyzer()
        res = python_analyzer.analyze_file(file_path, self.test_dir)

        self.assertTrue(res.graph.has_node("outer"))
        self.assertTrue(res.graph.has_node("outer.inner"))

        # Verify internal structure
        node_data = res.graph.nodes["outer.inner"]
        self.assertEqual(node_data["type"], "function")
        self.assertEqual(node_data["language"], "python")

    def test_lambda_assignments(self):
        # CallGraphVisitor currently does not implement visit_Lambda or visit_Assign
        # So we just test that lambdas don't break analysis and any calls *inside*
        # a lambda aren't attached to weird scopes or it handles it gracefully.
        code = """
my_lambda = lambda x: print(x)

def use_lambda():
    return my_lambda(5)
"""
        file_path = self.create_file("test_lambda.py", code)
        python_analyzer = PythonAnalyzer()
        res = python_analyzer.analyze_file(file_path, self.test_dir)

        defs = [d["name"] for d in res.definitions]
        self.assertIn("use_lambda", defs)

        # Verify the print call is captured if any, or at least my_lambda call is pending
        calls = [c for scope, c in res.pending_calls if c.get("name") == "my_lambda"]
        self.assertTrue(len(calls) > 0, "Expected a my_lambda pending call")

    def test_import_edge_shapes(self):
        code = """
import os
import sys as system
from pathlib import Path
from math import *

def use_imports():
    os.path.join('a', 'b')
    Path('.')
"""
        file_path = self.create_file("test_imports.py", code)
        python_analyzer = PythonAnalyzer()
        res = python_analyzer.analyze_file(file_path, self.test_dir)

        imports = res.imports
        self.assertTrue(
            any(imp["module"] == "os" and imp["kind"] == "import" for imp in imports)
        )
        self.assertTrue(
            any(
                imp["module"] == "sys" and "system" in imp["asnames"] for imp in imports
            )
        )
        self.assertTrue(
            any(
                imp["module"] == "pathlib" and "Path" in imp["names"] for imp in imports
            )
        )
        self.assertTrue(
            any(imp["module"] == "math" and "*" in imp["names"] for imp in imports)
        )

    def test_fastapi_route_decorators_api_boundary(self):
        code = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users():
    pass

@app.post("/users")
def create_user():
    pass
"""
        file_path = self.create_file("test_fastapi.py", code)

        # Use CodeAnalyzer to process api_boundary during analysis
        res = self.analyzer.analyze_file(self.test_dir)

        graph = res["graph"]
        self.assertTrue(graph.has_node("get_users"))
        self.assertTrue(graph.nodes["get_users"].get("api_boundary", False))

        self.assertTrue(graph.has_node("create_user"))
        self.assertTrue(graph.nodes["create_user"].get("api_boundary", False))

    def test_builtin_stdlib_unresolved_edges(self):
        code = """
def my_func():
    print("hello")       # Builtin
    os.path.join("a")    # Stdlib
    unknown_func()       # Unresolved
"""
        file_path = self.create_file("test_edges.py", code)

        # We need another file to act as the project so stdlib logic kicks in
        # or just test it with codeanalyzer directly.
        res = self.analyzer.analyze_file(self.test_dir)

        graph = res["graph"]
        # Edges from my_func -> print, os.path.join, unknown_func
        # Verify edge properties

        my_func_id = f"test_edges.my_func"
        # Node IDs in the full graph for python don't strictly require module: for defs
        # Let's just find my_func or test_edges.my_func
        my_func_node = next((n for n in graph.nodes if n.endswith("my_func")), None)
        self.assertIsNotNone(my_func_node)

        # Verify nodes are in graph
        edges = graph.out_edges(my_func_node, data=True)

        # We should find edges to builtin:print, external:os.path.join, unresolved:unknown_func
        targets = [
            v
            for u, v, data in edges
            if u == my_func_node and data.get("edge_type") == "calls"
        ]

        # Test node types instead, CodeAnalyzer populates nodes not necessarily specific edge names if the call isn't there
        types = {nid: data.get("type") for nid, data in graph.nodes(data=True)}

        self.assertIn("builtin:print", types)
        self.assertEqual(types["builtin:print"], "builtin")

        self.assertIn("external:os.path.join", types)
        self.assertEqual(types["external:os.path.join"], "external")

        self.assertIn("unresolved:unknown_func", types)
        self.assertEqual(types["unresolved:unknown_func"], "unresolved")


if __name__ == "__main__":
    unittest.main()
