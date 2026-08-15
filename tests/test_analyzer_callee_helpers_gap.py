"""Direct unit coverage for CallGraphVisitor._extract_callee and
._raw_callee_name in analyst/analyzer.py, which previously had no dedicated
test — only exercised indirectly through full-file CodeAnalyzer.analyze_file
integration tests in test_analyzer.py.

_extract_callee classifies a Call AST node into name/self_method/attribute
call-graph edge info; _raw_callee_name is the cheap callee-name extraction
used by the side-effect-call heuristic. A bug in either silently mis-wires
or drops call-graph edges without raising an error.

The JS analog (_Walker._classify_call in analyst/languages/javascript.py) is
already tested in tests/languages/test_javascript_parsing_helpers.py — this
file mirrors that test's case list so both language implementations stay
behaviorally aligned.
"""

import ast
import unittest

from analyst.analyzer import CallGraphVisitor


def _call_node(source: str) -> ast.Call:
    """Parse a single expression-statement line and return its Call node."""
    module = ast.parse(source)
    expr = module.body[0]
    assert isinstance(expr, ast.Expr)
    call = expr.value
    assert isinstance(call, ast.Call)
    return call


class TestExtractCallee(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_bare_name_call(self):
        self.assertEqual(
            self.visitor._extract_callee(_call_node("foo()")),
            {"kind": "name", "name": "foo"},
        )

    def test_single_level_attribute_call(self):
        self.assertEqual(
            self.visitor._extract_callee(_call_node("obj.method()")),
            {"kind": "attribute", "name": "method", "base": "obj", "parts": ["method"]},
        )

    def test_chained_attribute_call(self):
        self.assertEqual(
            self.visitor._extract_callee(_call_node("a.b.c()")),
            {"kind": "attribute", "name": "c", "base": "a", "parts": ["b", "c"]},
        )

    def test_self_method_call_inside_class(self):
        self.visitor.class_stack.append("MyClass")
        self.assertEqual(
            self.visitor._extract_callee(_call_node("self.method()")),
            {"kind": "self_method", "name": "method", "class": "MyClass"},
        )

    def test_cls_method_call_inside_class(self):
        self.visitor.class_stack.append("MyClass")
        self.assertEqual(
            self.visitor._extract_callee(_call_node("cls.method()")),
            {"kind": "self_method", "name": "method", "class": "MyClass"},
        )

    def test_self_call_outside_class_is_plain_attribute(self):
        # class_stack is empty (no enclosing class on the visitor) — must
        # not be misclassified as a self_method.
        self.assertEqual(
            self.visitor._extract_callee(_call_node("self.method()")),
            {"kind": "attribute", "name": "method", "base": "self", "parts": ["method"]},
        )

    def test_self_multi_level_attribute_is_not_self_method(self):
        # self.a.b() -> the attribute chain is two hops deep, so the
        # self_method shortcut (which requires exactly one hop) doesn't
        # apply even with a non-empty class_stack.
        self.visitor.class_stack.append("MyClass")
        self.assertEqual(
            self.visitor._extract_callee(_call_node("self.a.b()")),
            {"kind": "attribute", "name": "b", "base": "self", "parts": ["a", "b"]},
        )

    def test_chained_call_result_uses_rightmost_attr_with_no_base(self):
        # obj().method() -> func.value is itself a Call, not a Name, so the
        # attribute-chain walk bottoms out on a non-Name node. base is None
        # but the rightmost attribute name is still recorded so it shows up
        # in the graph somewhere.
        self.assertEqual(
            self.visitor._extract_callee(_call_node("obj().method()")),
            {"kind": "attribute", "name": "method", "base": None, "parts": ["method"]},
        )

    def test_subscript_call_returns_none(self):
        # d[0]() -- func is a Subscript, neither Name nor Attribute.
        self.assertIsNone(self.visitor._extract_callee(_call_node("d[0]()")))

    def test_plain_call_result_returns_none(self):
        # foo()() -- outer func is itself a Call (no attribute at all), so
        # classification bails out cleanly rather than mis-tagging it.
        self.assertIsNone(self.visitor._extract_callee(_call_node("foo()()")))


class TestRawCalleeName(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_bare_name_call(self):
        self.assertEqual(self.visitor._raw_callee_name(_call_node("foo()")), "foo")

    def test_single_level_attribute_call_returns_attr(self):
        self.assertEqual(
            self.visitor._raw_callee_name(_call_node("obj.method()")), "method"
        )

    def test_chained_attribute_call_returns_rightmost_attr_only(self):
        self.assertEqual(self.visitor._raw_callee_name(_call_node("a.b.c()")), "c")

    def test_self_method_call_returns_attr_name(self):
        self.assertEqual(
            self.visitor._raw_callee_name(_call_node("self.method()")), "method"
        )

    def test_subscript_call_returns_none(self):
        self.assertIsNone(self.visitor._raw_callee_name(_call_node("d[0]()")))

    def test_chained_call_result_returns_last_attr(self):
        self.assertEqual(
            self.visitor._raw_callee_name(_call_node("obj().method()")), "method"
        )

    def test_plain_call_result_returns_none(self):
        self.assertIsNone(self.visitor._raw_callee_name(_call_node("foo()()")))


if __name__ == "__main__":
    unittest.main()
