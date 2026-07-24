"""Direct unit coverage for CallGraphVisitor's callee-classification helpers,
which previously had no dedicated test — only exercised indirectly through
full-file CodeAnalyzer.analyze_file integration tests.

_raw_callee_name and _extract_callee classify a Call AST node (``foo()``,
``self.foo()``, ``obj.attr.foo()``) into the info dict that later feeds
_resolve_call, which decides whether a call becomes a builtin/external/
imported/self-method edge in the product's call graph. A misclassification
here is silent: it does not raise, it just produces a wrong or missing edge
in the graph the product visualizes.
"""

import ast
import unittest

from analyst.analyzer import CallGraphVisitor


def _parse_call(source: str) -> ast.Call:
    """Parse a one-line expression statement and return its Call node."""
    module = ast.parse(source)
    stmt = module.body[0]
    assert isinstance(stmt, ast.Expr)
    call = stmt.value
    assert isinstance(call, ast.Call)
    return call


class TestRawCalleeName(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_bare_name_call(self):
        node = _parse_call("foo()")
        self.assertEqual(self.visitor._raw_callee_name(node), "foo")

    def test_attribute_call_returns_rightmost_attr(self):
        node = _parse_call("obj.foo()")
        self.assertEqual(self.visitor._raw_callee_name(node), "foo")

    def test_chained_attribute_call_returns_rightmost_attr(self):
        node = _parse_call("a.b.c.foo()")
        self.assertEqual(self.visitor._raw_callee_name(node), "foo")

    def test_subscript_call_returns_none(self):
        node = _parse_call("handlers[0]()")
        self.assertIsNone(self.visitor._raw_callee_name(node))

    def test_call_result_call_returns_none(self):
        node = _parse_call("make_callable()()")
        self.assertIsNone(self.visitor._raw_callee_name(node))


class TestExtractCalleeNameKind(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_bare_name_call_is_kind_name(self):
        node = _parse_call("foo()")
        self.assertEqual(
            self.visitor._extract_callee(node), {"kind": "name", "name": "foo"}
        )

    def test_subscript_call_returns_none(self):
        node = _parse_call("handlers[0]()")
        self.assertIsNone(self.visitor._extract_callee(node))


class TestExtractCalleeSelfMethod(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")
        self.visitor.class_stack.append("MyClass")

    def test_self_dot_method_call(self):
        node = _parse_call("self.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "self_method", "name": "foo", "class": "MyClass"},
        )

    def test_cls_dot_method_call(self):
        node = _parse_call("cls.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "self_method", "name": "foo", "class": "MyClass"},
        )

    def test_self_dot_chained_attribute_is_not_self_method(self):
        # self.a.foo() has more than one part in the attribute chain, so it
        # must NOT be classified as a direct self-method call.
        node = _parse_call("self.a.foo()")
        result = self.visitor._extract_callee(node)
        self.assertEqual(result["kind"], "attribute")
        self.assertEqual(result["name"], "foo")
        self.assertEqual(result["base"], "self")
        self.assertEqual(result["parts"], ["a", "foo"])

    def test_self_method_outside_class_stack_is_attribute(self):
        # Without an enclosing class on the stack, self.foo() cannot be
        # resolved as a self-method and must fall back to "attribute".
        visitor = CallGraphVisitor("test.py")
        node = _parse_call("self.foo()")
        result = visitor._extract_callee(node)
        self.assertEqual(result["kind"], "attribute")
        self.assertEqual(result["base"], "self")


class TestExtractCalleeAttribute(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_simple_attribute_call(self):
        node = _parse_call("obj.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "attribute", "name": "foo", "base": "obj", "parts": ["foo"]},
        )

    def test_deeply_chained_attribute_call(self):
        node = _parse_call("a.b.c.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {
                "kind": "attribute",
                "name": "foo",
                "base": "a",
                "parts": ["b", "c", "foo"],
            },
        )

    def test_call_result_attribute_call_has_no_base(self):
        # make_obj().foo() -- the base is a Call, not a Name, so it can't be
        # resolved to a symbol; only the rightmost attr name is recorded.
        node = _parse_call("make_obj().foo()")
        result = self.visitor._extract_callee(node)
        self.assertEqual(result, {"kind": "attribute", "name": "foo", "base": None, "parts": ["foo"]})

    def test_subscript_base_attribute_call_has_no_base(self):
        node = _parse_call("handlers[0].foo()")
        result = self.visitor._extract_callee(node)
        self.assertEqual(result["kind"], "attribute")
        self.assertEqual(result["name"], "foo")
        self.assertIsNone(result["base"])


if __name__ == "__main__":
    unittest.main()
