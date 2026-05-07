import ast
import unittest
import os
import shutil
import tempfile
import sys
from unittest.mock import patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst import analyzer as analyzer_mod
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
        # self.method_b() now resolves to the qualified MyClass.method_b
        # instead of the bare attribute name (eliminates a gray "ref" node).
        self.assertTrue(graph.has_edge("MyClass.method_a", "MyClass.method_b"))
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

    def test_dict_get_does_not_flag_side_effect_boundary(self):
        """`dict.get` / `cache.get` must not be treated as a network call."""
        code = """
def lookup(cache, key):
    value = cache.get(key)
    return value if value is not None else {}.get("fallback")
"""
        file_path = self.create_file("dict_get.py", code)
        result = self.analyzer.analyze_file(file_path)

        node = result["graph"].nodes["lookup"]
        self.assertFalse(
            node["side_effect_boundary"],
            "dict.get/cache.get should not flag side_effect_boundary",
        )
        self.assertFalse(node["api_boundary"])

    def test_real_io_call_still_flags_side_effect_boundary(self):
        """Genuine I/O like open() must still be detected."""
        code = """
def read_file(path):
    with open(path) as f:
        return f.read()
"""
        file_path = self.create_file("real_io.py", code)
        result = self.analyzer.analyze_file(file_path)

        node = result["graph"].nodes["read_file"]
        self.assertTrue(node["side_effect_boundary"])


class TestCallResolution(unittest.TestCase):
    """Tests for the two-pass resolver that classifies call targets so the
    frontend can render meaningful colored nodes instead of gray "ref" stubs.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.analyzer = CodeAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _write(self, path: str, content: str) -> str:
        full = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full) or self.test_dir, exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return full

    def _types(self, graph) -> dict[str, str]:
        return {nid: data.get("type") for nid, data in graph.nodes(data=True)}

    def test_builtins_get_builtin_type_not_default(self):
        """`print()`, `len()` should be tagged ``builtin`` so they render in
        the dedicated style instead of the gray fallback.
        """
        path = self._write(
            "simple.py",
            "def hello():\n    print(len([1, 2, 3]))\n",
        )
        result = self.analyzer.analyze_file(path)
        types = self._types(result["graph"])

        self.assertEqual(types["hello"], "function")
        self.assertEqual(types.get("builtin:print"), "builtin")
        self.assertEqual(types.get("builtin:len"), "builtin")
        # No node may be left with the empty/default type.
        for nid, t in types.items():
            self.assertTrue(t, f"node {nid!r} has empty type")
            self.assertNotEqual(t, "default", f"node {nid!r} fell back to default")

    def test_self_method_resolves_to_qualified_name(self):
        """`self.foo()` should link to ``Class.foo`` (the real definition),
        not create a separate gray ``foo`` reference node."""
        path = self._write(
            "cls.py",
            "class A:\n"
            "    def a(self):\n"
            "        self.b()\n"
            "    def b(self):\n"
            "        pass\n",
        )
        result = self.analyzer.analyze_file(path)
        graph = result["graph"]

        self.assertTrue(graph.has_edge("A.a", "A.b"))
        # The method is the real definition node, not a stub.
        self.assertEqual(graph.nodes["A.b"]["type"], "function")
        # No bare 'b' stub from the old `node.func.attr`-only logic.
        self.assertFalse(graph.has_node("b"))

    def test_stdlib_attribute_call_tagged_external(self):
        """`os.path.exists(...)` is tagged external (orange), not unresolved."""
        path = self._write(
            "uses_os.py",
            "import os\ndef check(p):\n    return os.path.exists(p)\n",
        )
        result = self.analyzer.analyze_file(path)
        types = self._types(result["graph"])

        ext_ids = [nid for nid, t in types.items() if t == "external"]
        self.assertTrue(
            ext_ids,
            f"expected an external node for os.path.exists, got types={types}",
        )

    def test_local_imported_call_links_to_definition(self):
        """A function imported from another local module must edge-link to the
        canonical definition (not a duplicate stub) when both live in the
        analyzed directory."""
        self._write("utils.py", "def helper():\n    return 1\n")
        self._write(
            "main.py",
            "from utils import helper\ndef run():\n    return helper()\n",
        )
        result = self.analyzer.analyze_file(self.test_dir)
        graph = result["graph"]

        self.assertTrue(graph.has_node("helper"))
        self.assertEqual(graph.nodes["helper"]["type"], "function")
        self.assertTrue(graph.has_edge("run", "helper"))

    def test_module_nodes_added_for_each_file(self):
        """Each file with code becomes a `module:<dotted>` node and contains
        its top-level defs; cross-file local imports become module-to-module
        edges so the user can see the high-level project shape."""
        self._write("utils.py", "def helper():\n    return 1\n")
        self._write(
            "main.py",
            "from utils import helper\ndef run():\n    return helper()\n",
        )
        result = self.analyzer.analyze_file(self.test_dir)
        graph = result["graph"]

        self.assertTrue(graph.has_node("module:utils"))
        self.assertTrue(graph.has_node("module:main"))
        self.assertEqual(graph.nodes["module:utils"]["type"], "module")
        self.assertTrue(graph.has_edge("module:utils", "helper"))
        self.assertTrue(graph.has_edge("module:main", "run"))
        self.assertTrue(graph.has_edge("module:main", "module:utils"))

    def test_no_module_node_for_file_without_code(self):
        """A constants-only file shouldn't conjure a meaningless module node;
        upload validation in the router relies on graph emptiness."""
        self._write("consts.py", "ANSWER = 42\n")
        result = self.analyzer.analyze_file(self.test_dir)
        self.assertEqual(result["graph"].number_of_nodes(), 0)

    def test_no_default_typed_nodes_in_complex_file(self):
        """End-to-end sanity: a realistic small file produces zero nodes that
        fall back to the gray default style."""
        path = self._write(
            "real.py",
            "import json\n"
            "from typing import Any\n"
            "\n"
            "def load(s):\n"
            "    return json.loads(s)\n"
            "\n"
            "class Box:\n"
            "    def __init__(self, v):\n"
            "        self.v = v\n"
            "    def show(self):\n"
            "        print(self.v)\n"
            "        return str(self.v)\n",
        )
        result = self.analyzer.analyze_file(path)
        for nid, data in result["graph"].nodes(data=True):
            t = data.get("type")
            self.assertTrue(t, f"node {nid!r} has empty type")
            self.assertNotEqual(t, "default", f"node {nid!r} fell back to default")


class TestCodeAnalyzerEncoding(unittest.TestCase):
    """Regression tests for non-UTF-8 Python source handling.

    Before the fix, a single non-UTF-8 .py file anywhere in an uploaded
    project raised UnicodeDecodeError out of _analyze_single_file. The
    exception escaped _analyze_directory's `except OSError:` (UnicodeDecodeError
    is a ValueError, not an OSError) and surfaced as a 500 to the user.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.analyzer = CodeAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def write_bytes(self, path: str, data: bytes) -> str:
        full_path = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full_path) or self.test_dir, exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        return full_path

    def test_pep263_cp1252_file_parses_successfully(self):
        """A file with a PEP 263 coding declaration should be parsed."""
        source = b"# -*- coding: cp1252 -*-\ndef greet():\n    return 'caf\xe9'\n"
        file_path = self.write_bytes("legacy.py", source)

        result = self.analyzer.analyze_file(file_path)

        self.assertNotIn("error", result)
        def_names = [d["name"] for d in result["definitions"]]
        self.assertIn("greet", def_names)

    def test_non_utf8_file_without_declaration_is_skipped_not_fatal(self):
        """One bad file must not nuke the whole directory analysis."""
        self.write_bytes("good.py", b"def a(): pass\n")
        self.write_bytes("bad.py", b"def b():\n    return 'caf\xe9'\n")

        result = self.analyzer.analyze_file(self.test_dir)

        graph = result["graph"]
        self.assertTrue(graph.has_node("a"))
        self.assertFalse(graph.has_node("b"))
        self.assertTrue(
            any("bad.py" in err for err in result["errors"]),
            f"expected an error entry mentioning bad.py, got {result['errors']}",
        )

    def test_single_bad_file_returns_error_not_exception(self):
        """Single-file mode must degrade to an error dict, not raise."""
        file_path = self.write_bytes("solo.py", b"def b():\n    return 'caf\xe9'\n")

        result = self.analyzer.analyze_file(file_path)

        self.assertIn("error", result)

    def test_utf8_bom_file_parses_successfully(self):
        """Characterization test: BOM-prefixed UTF-8 is valid Python source."""
        source = b"\xef\xbb\xbfdef bommed(): pass\n"
        file_path = self.write_bytes("bom.py", source)

        result = self.analyzer.analyze_file(file_path)

        self.assertNotIn("error", result)
        def_names = [d["name"] for d in result["definitions"]]
        self.assertIn("bommed", def_names)

    def test_null_byte_in_source_is_skipped(self):
        """ast.parse raises ValueError for null bytes; must be caught."""
        source = b"def ok():\n    return 0\n\x00\n"
        self.write_bytes("good.py", b"def a(): pass\n")
        self.write_bytes("nullish.py", source)

        result = self.analyzer.analyze_file(self.test_dir)

        graph = result["graph"]
        self.assertTrue(graph.has_node("a"))
        self.assertTrue(
            any("nullish.py" in err for err in result["errors"]),
            f"expected an error entry mentioning nullish.py, got {result['errors']}",
        )

    def test_extract_dependencies_non_utf8_file(self):
        """extract_dependencies must not raise on a non-UTF-8 file."""
        file_path = self.write_bytes("legacy.py", b"import os\nx = 'caf\xe9'\n")

        result = self.analyzer.extract_dependencies(file_path)

        self.assertIn("error", result)


class TestASTCaching(unittest.TestCase):
    """Operation-count regression tests for the content-hash AST cache.

    These tests assert big-O behaviour (repeat work goes to zero) instead of
    wall-clock thresholds, which are unreliable on shared CI runners.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        analyzer_mod._ast_cache_clear()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        analyzer_mod._ast_cache_clear()

    def _write(self, name: str, body: str) -> str:
        path = os.path.join(self.test_dir, name)
        os.makedirs(os.path.dirname(path) or self.test_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path

    def test_pass1_unique_files_each_parse(self):
        for i in range(50):
            self._write(f"u_{i}.py", f"def f_{i}():\n    return {i}\n")

        with patch.object(ast, "parse", wraps=ast.parse) as spy:
            CodeAnalyzer().analyze_file(self.test_dir)
            self.assertEqual(spy.call_count, 50)

    def test_pass2_identical_content_zero_reparse(self):
        body = "def f():\n    return 1\n"
        for i in range(50):
            self._write(f"id_{i}.py", body)

        # Warm: 50 identical files share one cache entry, so 1 actual parse.
        CodeAnalyzer().analyze_file(self.test_dir)

        with patch.object(ast, "parse", wraps=ast.parse) as spy:
            CodeAnalyzer().analyze_file(self.test_dir)
            self.assertEqual(spy.call_count, 0)

    def test_pass3_modify_one_file_one_parse(self):
        body = "def f():\n    return 1\n"
        paths = [self._write(f"m_{i}.py", body) for i in range(50)]

        # Warm.
        CodeAnalyzer().analyze_file(self.test_dir)

        # Change exactly one file's content.
        with open(paths[0], "w", encoding="utf-8") as f:
            f.write("def changed():\n    return 99\n")

        with patch.object(ast, "parse", wraps=ast.parse) as spy:
            CodeAnalyzer().analyze_file(self.test_dir)
            self.assertEqual(spy.call_count, 1)

    def test_pass4_path_independence(self):
        body = "def f():\n    return 1\n"
        self._write("a.py", body)

        # Warm with a.py.
        CodeAnalyzer().analyze_file(self.test_dir)

        # Add b.py with identical bytes — content key is the same, so a hit.
        self._write("b.py", body)

        with patch.object(ast, "parse", wraps=ast.parse) as spy:
            CodeAnalyzer().analyze_file(self.test_dir)
            self.assertEqual(spy.call_count, 0)

    def test_visitor_tags_correct_file_path(self):
        """Correctness guard: identical bytes across two paths must still
        produce nodes tagged with their actual file paths. This would fail if
        a future change cached the per-file DiGraph instead of the ast.Module.

        Analyze the files independently — directory composition collapses
        same-named nodes via nx.compose_all, which is unrelated to caching.
        """
        body = "def shared():\n    return 1\n"
        path_a = self._write("a.py", body)
        path_b = self._write("b.py", body)

        # First call populates the cache; second call must hit it but still
        # tag the node with path_b (proves the cached ast.Module is reused
        # without leaking path_a's identity into path_b's graph).
        result_a = CodeAnalyzer().analyze_file(path_a)
        result_b = CodeAnalyzer().analyze_file(path_b)

        files_a = {data.get("file") for _, data in result_a["graph"].nodes(data=True)}
        files_b = {data.get("file") for _, data in result_b["graph"].nodes(data=True)}
        self.assertEqual(files_a, {path_a})
        self.assertEqual(files_b, {path_b})

        # Sanity-check: the second call did hit the cache (zero ast.parse calls).
        analyzer_mod._ast_cache_clear()
        CodeAnalyzer().analyze_file(path_a)  # warm
        with patch.object(ast, "parse", wraps=ast.parse) as spy:
            CodeAnalyzer().analyze_file(path_b)
            self.assertEqual(spy.call_count, 0)

    def test_syntax_error_not_cached(self):
        """SyntaxError paths must continue to surface every call, never
        replayed from cache (v1 design: only successful parses are cached).
        """
        bad_path = self._write("broken.py", "def incomplete(")

        with patch.object(ast, "parse", wraps=ast.parse) as spy:
            CodeAnalyzer().analyze_file(bad_path)
            CodeAnalyzer().analyze_file(bad_path)
            self.assertEqual(spy.call_count, 2)


if __name__ == "__main__":
    unittest.main()
