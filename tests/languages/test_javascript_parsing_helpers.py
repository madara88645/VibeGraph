"""Direct unit coverage for analyst.languages.javascript private helpers that
previously had no dedicated test — only exercised indirectly through
full-file JavaScriptAnalyzer.analyze_file fixture tests in test_javascript.py.

_Walker._classify_call decides how a call expression is tagged (bare name,
attribute/member chain, or ``this.method()``), which drives call-graph edge
resolution. _parse_import_statement and _parse_require_call turn ESM/CJS
import syntax into the Python-shaped import records the orchestrator
consumes for cross-file resolution. A bug in any of these silently
mis-wires or drops call-graph edges without raising an error, mirroring the
gap already backfilled for the Python analyzer in
test_analyzer_parsing_helpers_gap.py.
"""

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analyst.languages.javascript import (
    _Walker,
    _parse_import_statement,
    _parse_require_call,
)
from analyst.tree_sitter_loader import get_parser


def _parse(source: str):
    parser = get_parser("javascript")
    return parser.parse(source.encode("utf-8"))


def _find_first(node, node_type: str):
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == node_type:
            return current
        stack.extend(reversed(current.children))
    return None


class TestClassifyCall(unittest.TestCase):
    def _classify(self, source: str, in_class: bool = False):
        tree = _parse(source)
        call_node = _find_first(tree.root_node, "call_expression")
        walker = _Walker(file_path="<test>", source=source.encode("utf-8"), language_id="javascript")
        if in_class:
            walker.class_stack.append("MyClass")
        return walker._classify_call(call_node)

    def test_bare_identifier_call(self):
        self.assertEqual(self._classify("foo();"), {"kind": "name", "name": "foo"})

    def test_single_level_member_call(self):
        self.assertEqual(
            self._classify("obj.method();"),
            {"kind": "attribute", "name": "method", "base": "obj", "parts": ["method"]},
        )

    def test_chained_member_call(self):
        self.assertEqual(
            self._classify("a.b.c();"),
            {"kind": "attribute", "name": "c", "base": "a", "parts": ["b", "c"]},
        )

    def test_this_call_inside_class_is_self_method(self):
        self.assertEqual(
            self._classify("class X { m() { this.method(); } }", in_class=True),
            {"kind": "self_method", "name": "method", "class": "MyClass"},
        )

    def test_this_call_outside_class_is_plain_attribute(self):
        # No enclosing class on the walker's class_stack — must not be
        # misclassified as a self_method.
        self.assertEqual(
            self._classify("this.method();", in_class=False),
            {"kind": "attribute", "name": "method", "base": None, "parts": ["method"]},
        )

    def test_computed_member_call_is_unclassified(self):
        # obj[key]() — the callee is a subscript_expression, not a
        # member_expression/identifier, so classification must bail out
        # cleanly rather than mis-tagging it.
        self.assertIsNone(self._classify("obj[key]();"))


class TestParseImportStatement(unittest.TestCase):
    def _entries(self, source: str, local_modules=frozenset()):
        tree = _parse(source)
        node = _find_first(tree.root_node, "import_statement")
        return _parse_import_statement(node, source.encode("utf-8"), local_modules)

    def test_default_import(self):
        result = self._entries('import Foo from "./foo";')
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["kind"], "from")
        self.assertEqual(entry["module"], "./foo")
        self.assertEqual(entry["names"], ["default"])
        self.assertEqual(entry["asnames"], ["Foo"])
        self.assertTrue(entry["is_local"])

    def test_namespace_import(self):
        result = self._entries('import * as ns from "./mod";')
        entry = result[0]
        self.assertEqual(entry["kind"], "import")
        self.assertEqual(entry["module"], "./mod")
        self.assertEqual(entry["names"], ["./mod"])
        self.assertEqual(entry["asnames"], ["ns"])

    def test_named_imports_with_alias(self):
        result = self._entries('import { a, b as c } from "pkg";')
        entry = result[0]
        self.assertEqual(entry["kind"], "from")
        self.assertEqual(entry["module"], "pkg")
        self.assertEqual(entry["names"], ["a", "b"])
        self.assertEqual(entry["asnames"], ["a", "c"])

    def test_named_import_module_locality_depends_on_local_modules(self):
        result = self._entries('import { a } from "pkg";', local_modules=frozenset({"pkg"}))
        self.assertTrue(result[0]["is_local"])
        result = self._entries('import { a } from "pkg";', local_modules=frozenset())
        self.assertFalse(result[0]["is_local"])

    def test_side_effect_import_returns_empty_list(self):
        self.assertEqual(self._entries('import "./side-effects";'), [])


class TestParseRequireCall(unittest.TestCase):
    def _parse_require(self, source: str, local_modules=frozenset()):
        tree = _parse(source)
        node = _find_first(tree.root_node, "call_expression")
        return _parse_require_call(node, source.encode("utf-8"), local_modules)

    def test_simple_binding(self):
        entry = self._parse_require('const foo = require("./foo");')
        self.assertEqual(
            entry,
            {
                "kind": "import",
                "module": "./foo",
                "names": ["./foo"],
                "asnames": ["foo"],
                "is_local": True,
                "level": 0,
            },
        )

    def test_destructured_binding(self):
        entry = self._parse_require('const { a, b: c } = require("pkg");')
        self.assertEqual(entry["kind"], "from")
        self.assertEqual(entry["module"], "pkg")
        self.assertEqual(entry["names"], ["a", "b"])
        self.assertEqual(entry["asnames"], ["a", "c"])
        self.assertFalse(entry["is_local"])

    def test_bare_require_with_no_binding_returns_none(self):
        self.assertIsNone(self._parse_require('require("./side-effect");'))

    def test_non_require_call_returns_none(self):
        self.assertIsNone(self._parse_require("const foo = other();"))


if __name__ == "__main__":
    unittest.main()
