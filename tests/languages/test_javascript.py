import unittest
import os
import shutil
import tempfile
from unittest.mock import patch

from analyst.analyzer import CodeAnalyzer
from analyst.languages.javascript import JavaScriptAnalyzer
from analyst.languages.typescript import TypeScriptAnalyzer


class TestJavaScriptAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_javascript_analyzer_features(self):
        # We test various features using our fixture files:
        # - function declarations (named, async, generator)
        # - arrow functions assigned to const
        # - named exports, default exports
        # - ES6 imports (default, named, namespace)
        # - CommonJS require() bindings
        # - class declarations with extends
        # - class methods and static methods
        # - async arrow functions

        fixture_dir = os.path.join(
            os.path.dirname(__file__), "..", "fixtures", "javascript_sample"
        )

        result = self.analyzer.analyze_file(fixture_dir)
        graph = result["graph"]

        # 1. Assert graph contains expected function/class/module nodes
        expected_nodes = [
            # from models.js
            "User",
            "User.constructor",
            "User.getName",
            "User.getRole",
            "Admin",
            "Admin.constructor",
            "Admin.getRole",
            # from api.js
            "fetchAdminData",
            # (Note: default export methods show up with specific local IDs depending on implementation details,
            # but we can check fetchAdminData for arrow function export)
            # from utils.js
            "setupUtils",
            # from config.js
            "generator",
            "asyncArrow",
            # from index.js
            "main",
            "helper",
            # modules
            "module:models",
            "module:api",
            "module:config",
            "module:index",
            "module:utils",
        ]

        for node in expected_nodes:
            self.assertTrue(graph.has_node(node), f"Graph missing node: {node}")

        # 2. Assert import/call edges
        # main calls setupUtils, fetchAdminData, api.fetchData
        self.assertTrue(graph.has_edge("main", "setupUtils"))
        self.assertTrue(graph.has_edge("main", "fetchAdminData"))

        # Test local default export object method logic
        # main -> local:./api.js.default.fetchData
        found_fetch_data_call = False
        for _, v in graph.edges("main"):
            if "fetchData" in v:
                found_fetch_data_call = True
                break
        self.assertTrue(
            found_fetch_data_call, "Could not find edge from main to fetchData"
        )

        # setupUtils calls fs.readFileSync (external)
        self.assertTrue(graph.has_edge("setupUtils", "external:fs.readFileSync"))

        # modules point to their top-level definitions
        self.assertTrue(graph.has_edge("module:models", "User"))
        self.assertTrue(graph.has_edge("module:models", "Admin"))
        self.assertTrue(graph.has_edge("module:api", "fetchAdminData"))
        self.assertTrue(graph.has_edge("module:config", "generator"))
        self.assertTrue(graph.has_edge("module:config", "asyncArrow"))
        self.assertTrue(graph.has_edge("module:index", "main"))
        self.assertTrue(graph.has_edge("module:index", "helper"))
        self.assertTrue(graph.has_edge("module:utils", "setupUtils"))


class TestJavaScriptPerformanceRegression(unittest.TestCase):
    """Operation-count regression tests for JS/TS local-module discovery."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.analyzer = CodeAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _write(self, rel_path: str, body: str) -> str:
        path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
        return path

    def _seed_medium_js_fixture(self, file_count: int = 40) -> None:
        self._write("core.js", "export function helper() { return 1; }\n")
        for i in range(file_count):
            self._write(
                f"feature_{i}.js",
                (
                    "import { helper } from './core';\n"
                    f"export function f{i}() {{ return helper() + {i}; }}\n"
                ),
            )

    def test_local_module_scan_count_is_constant_per_language(self):
        """Big-O guard: tree scan count must be O(languages), not O(files)."""
        self._seed_medium_js_fixture(file_count=60)

        js_scans = {"count": 0}
        ts_scans = {"count": 0}

        js_original = JavaScriptAnalyzer.get_local_modules
        ts_original = TypeScriptAnalyzer.get_local_modules

        def _wrapped_js(self, project_root):
            js_scans["count"] += 1
            return js_original(self, project_root)

        def _wrapped_ts(self, project_root):
            ts_scans["count"] += 1
            return ts_original(self, project_root)

        with (
            patch.object(JavaScriptAnalyzer, "get_local_modules", _wrapped_js),
            patch.object(TypeScriptAnalyzer, "get_local_modules", _wrapped_ts),
        ):
            result = self.analyzer.analyze_file(self.test_dir)

        graph = result["graph"]
        self.assertTrue(graph.has_edge("f0", "helper"))
        self.assertTrue(graph.has_edge("f59", "helper"))
        self.assertEqual(graph.nodes["helper"]["type"], "function")
        self.assertEqual(js_scans["count"], 1)
        self.assertEqual(ts_scans["count"], 0)
