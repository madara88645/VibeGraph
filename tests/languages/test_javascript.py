import unittest
import os

from analyst.analyzer import CodeAnalyzer


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
