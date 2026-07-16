"""Direct unit coverage for CallGraphVisitor's decorator-name and
nesting-depth helpers, which previously had no dedicated test — only
exercised indirectly through full-file CodeAnalyzer.analyze_file
integration tests.

_decorator_name resolves a decorator AST node to its dotted name (used to
detect API-boundary decorators like @app.route); _max_nesting_depth computes
the deepest control-flow nesting inside a function body (surfaced in the UI
as a complexity signal). Both are pure AST-node -> value functions with no
I/O, so a regression here silently mis-tags nodes without raising an error.
"""

import ast
import unittest

from analyst.analyzer import CallGraphVisitor


def _parse_single_decorator(source: str) -> ast.expr:
    """Parse a one-line snippet like '@a.b.c' and return the decorator node."""
    module = ast.parse(source + "\ndef f(): pass\n")
    func = module.body[0]
    assert isinstance(func, ast.FunctionDef)
    return func.decorator_list[0]


def _parse_function_body(source: str) -> ast.FunctionDef:
    module = ast.parse(source)
    func = module.body[0]
    assert isinstance(func, ast.FunctionDef)
    return func


class TestDecoratorName(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_simple_name_decorator(self):
        node = _parse_single_decorator("@staticmethod")
        self.assertEqual(self.visitor._decorator_name(node), "staticmethod")

    def test_dotted_attribute_decorator(self):
        node = _parse_single_decorator("@app.route")
        self.assertEqual(self.visitor._decorator_name(node), "app.route")

    def test_deeply_dotted_attribute_decorator(self):
        node = _parse_single_decorator("@a.b.c.d")
        self.assertEqual(self.visitor._decorator_name(node), "a.b.c.d")

    def test_call_decorator_unwraps_to_underlying_name(self):
        node = _parse_single_decorator('@app.route("/x")')
        self.assertEqual(self.visitor._decorator_name(node), "app.route")

    def test_call_decorator_with_plain_name(self):
        node = _parse_single_decorator("@lru_cache()")
        self.assertEqual(self.visitor._decorator_name(node), "lru_cache")

    def test_unsupported_node_type_returns_empty_string(self):
        # A subscript decorator (e.g. @registry[0]) isn't Name/Attribute/Call.
        node = _parse_single_decorator("@registry[0]")
        self.assertEqual(self.visitor._decorator_name(node), "")


class TestMaxNestingDepth(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_flat_function_has_zero_nesting(self):
        func = _parse_function_body("def f():\n    x = 1\n    return x\n")
        self.assertEqual(self.visitor._max_nesting_depth(func), 0)

    def test_single_if_has_depth_one(self):
        func = _parse_function_body("def f():\n    if True:\n        x = 1\n")
        self.assertEqual(self.visitor._max_nesting_depth(func), 1)

    def test_nested_if_for_while_accumulates_depth(self):
        source = (
            "def f():\n"
            "    if True:\n"
            "        for i in range(3):\n"
            "            while i:\n"
            "                x = 1\n"
        )
        func = _parse_function_body(source)
        self.assertEqual(self.visitor._max_nesting_depth(func), 3)

    def test_takes_deepest_of_multiple_sibling_branches(self):
        source = (
            "def f():\n"
            "    if True:\n"
            "        x = 1\n"
            "    if False:\n"
            "        for i in range(3):\n"
            "            if i:\n"
            "                y = 2\n"
        )
        func = _parse_function_body(source)
        self.assertEqual(self.visitor._max_nesting_depth(func), 3)

    def test_try_except_counts_as_nesting(self):
        source = (
            "def f():\n    try:\n        x = 1\n    except Exception:\n        pass\n"
        )
        func = _parse_function_body(source)
        self.assertEqual(self.visitor._max_nesting_depth(func), 1)


if __name__ == "__main__":
    unittest.main()
