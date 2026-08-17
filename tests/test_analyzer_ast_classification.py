"""Direct unit coverage for CallGraphVisitor's call-target classifier and
per-definition metadata builder, which previously had no dedicated test —
only exercised indirectly through full-file CodeAnalyzer.analyze_file
integration tests in test_analyzer.py.

_extract_callee classifies a Call AST node into bare-name / self-method /
attribute-chain / unresolvable-chained-call info dicts, and feeds the
pending_calls list that the second graph-resolution pass consumes directly
-- a misclassification here silently mis-wires or drops call-graph edges
without raising an error. _metadata_for_definition computes loc,
nesting_depth, dependency_count, and public_api from a def/class AST node;
these numbers drive learning-path ranking (see
app/services/learning_path.py's _complexity_penalty and _is_public_api),
so an off-by-one or wrong-branch here silently skews rankings rather than
crashing.

Both are pure AST-node -> value functions with no I/O.
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


def _parse_function_def(source: str) -> ast.FunctionDef:
    module = ast.parse(source)
    func = module.body[0]
    assert isinstance(func, ast.FunctionDef)
    return func


def _parse_class_def(source: str) -> ast.ClassDef:
    module = ast.parse(source)
    cls = module.body[0]
    assert isinstance(cls, ast.ClassDef)
    return cls


class TestExtractCalleeBareName(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_bare_name_call(self):
        node = _parse_call("foo()")
        self.assertEqual(self.visitor._extract_callee(node), {"kind": "name", "name": "foo"})

    def test_bare_name_call_with_args_is_ignored(self):
        # Arguments shouldn't affect classification, only the func target.
        node = _parse_call("foo(1, 2, kw=3)")
        self.assertEqual(self.visitor._extract_callee(node), {"kind": "name", "name": "foo"})


class TestExtractCalleeSelfMethod(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_self_dot_method_inside_class_is_self_method(self):
        self.visitor.class_stack = ["MyClass"]
        node = _parse_call("self.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "self_method", "name": "foo", "class": "MyClass"},
        )

    def test_cls_dot_method_inside_class_is_self_method(self):
        self.visitor.class_stack = ["MyClass"]
        node = _parse_call("cls.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "self_method", "name": "foo", "class": "MyClass"},
        )

    def test_self_method_uses_innermost_class_on_stack(self):
        self.visitor.class_stack = ["Outer", "Inner"]
        node = _parse_call("self.foo()")
        result = self.visitor._extract_callee(node)
        self.assertEqual(result["class"], "Inner")

    def test_self_dot_method_outside_class_is_attribute(self):
        # No class_stack -> "self" is just a regular attribute base, not a
        # method resolved against a known class.
        self.visitor.class_stack = []
        node = _parse_call("self.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "attribute", "name": "foo", "base": "self", "parts": ["foo"]},
        )

    def test_self_dot_multi_attr_chain_is_not_self_method(self):
        # self.a.foo() has len(parts) == 2, so the self_method fast-path
        # (which requires exactly one attribute hop) must not fire.
        self.visitor.class_stack = ["MyClass"]
        node = _parse_call("self.a.foo()")
        result = self.visitor._extract_callee(node)
        self.assertEqual(result["kind"], "attribute")
        self.assertEqual(result["base"], "self")
        self.assertEqual(result["parts"], ["a", "foo"])


class TestExtractCalleeAttributeChain(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_single_attribute_call(self):
        node = _parse_call("obj.foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "attribute", "name": "foo", "base": "obj", "parts": ["foo"]},
        )

    def test_deep_attribute_chain_call(self):
        node = _parse_call("a.b.c.foo()")
        result = self.visitor._extract_callee(node)
        self.assertEqual(result["kind"], "attribute")
        self.assertEqual(result["name"], "foo")
        self.assertEqual(result["base"], "a")
        self.assertEqual(result["parts"], ["b", "c", "foo"])


class TestExtractCalleeEdgeCases(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_chained_call_func_paren_x_paren(self):
        # func()(x): outer Call's .func is itself a Call, not Name/Attribute.
        node = _parse_call("func()(x)")
        self.assertIsNone(self.visitor._extract_callee(node))

    def test_subscript_then_call(self):
        # registry[0](): .func is a Subscript, not Name/Attribute.
        node = _parse_call("registry[0]()")
        self.assertIsNone(self.visitor._extract_callee(node))

    def test_attribute_chain_rooted_in_call_still_records_rightmost_name(self):
        # get_obj().foo(): the base of the attribute chain is a Call, not a
        # Name, so `base` is None but the rightmost attr name is preserved.
        node = _parse_call("get_obj().foo()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "attribute", "name": "foo", "base": None, "parts": ["foo"]},
        )

    def test_attribute_chain_rooted_in_subscript_still_records_rightmost_name(self):
        node = _parse_call("items[0].foo()")
        result = self.visitor._extract_callee(node)
        self.assertEqual(result["kind"], "attribute")
        self.assertEqual(result["name"], "foo")
        self.assertIsNone(result["base"])

    def test_lambda_immediately_invoked_returns_none(self):
        # (lambda: 1)(): .func is a Lambda, not Name/Attribute.
        node = _parse_call("(lambda: 1)()")
        self.assertIsNone(self.visitor._extract_callee(node))


class TestMetadataForDefinition(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_loc_single_line_function(self):
        func = _parse_function_def("def f(): pass\n")
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertEqual(meta["loc"], 1)

    def test_loc_multi_line_function(self):
        source = "def f():\n    x = 1\n    y = 2\n    return x + y\n"
        func = _parse_function_def(source)
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertEqual(meta["loc"], 4)

    def test_end_lineno_matches_node_end_lineno_for_parsed_source(self):
        func = _parse_function_def("def f():\n    x = 1\n    return x\n")
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertEqual(meta["end_lineno"], func.end_lineno)
        self.assertEqual(meta["end_lineno"], 3)

    def test_dependency_count_counts_unique_callee_names(self):
        source = "def f():\n    foo()\n    bar()\n    foo()\n"
        func = _parse_function_def(source)
        meta = self.visitor._metadata_for_definition(func, "f")
        # foo/bar dedupe by name (a set), even though foo() appears twice.
        self.assertEqual(meta["dependency_count"], 2)

    def test_dependency_count_zero_when_no_calls(self):
        func = _parse_function_def("def f():\n    x = 1\n    return x\n")
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertEqual(meta["dependency_count"], 0)

    def test_nesting_depth_delegates_to_max_nesting_depth(self):
        source = "def f():\n    if True:\n        for i in range(3):\n            x = i\n"
        func = _parse_function_def(source)
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertEqual(meta["nesting_depth"], 2)

    def test_public_api_true_for_plain_name(self):
        func = _parse_function_def("def helper(): pass\n")
        meta = self.visitor._metadata_for_definition(func, "helper")
        self.assertTrue(meta["public_api"])

    def test_public_api_false_for_leading_underscore(self):
        func = _parse_function_def("def _helper(): pass\n")
        meta = self.visitor._metadata_for_definition(func, "_helper")
        self.assertFalse(meta["public_api"])

    def test_public_api_checks_only_final_dotted_segment(self):
        # Dotted qualified names (Class.method) should only look at the
        # last segment when deciding public/private.
        func = _parse_function_def("def m(self): pass\n")
        meta = self.visitor._metadata_for_definition(func, "PublicClass._private_method")
        self.assertFalse(meta["public_api"])
        meta2 = self.visitor._metadata_for_definition(func, "_PrivateClass.public_method")
        self.assertTrue(meta2["public_api"])

    def test_api_boundary_true_for_route_decorator(self):
        func = _parse_function_def(
            '@app.route("/x")\ndef handler(): pass\n'
        )
        meta = self.visitor._metadata_for_definition(func, "handler")
        self.assertTrue(meta["api_boundary"])
        self.assertTrue(meta["side_effect_boundary"])

    def test_api_boundary_false_when_no_route_decorator(self):
        func = _parse_function_def("def plain(): pass\n")
        meta = self.visitor._metadata_for_definition(func, "plain")
        self.assertFalse(meta["api_boundary"])

    def test_side_effect_boundary_true_for_side_effect_module_import(self):
        source = "def f():\n    import os\n    return os.getcwd()\n"
        func = _parse_function_def(source)
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertTrue(meta["side_effect_boundary"])
        self.assertFalse(meta["api_boundary"])

    def test_side_effect_boundary_true_for_side_effect_call_name(self):
        source = "def f():\n    open('x.txt')\n"
        func = _parse_function_def(source)
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertTrue(meta["side_effect_boundary"])

    def test_side_effect_boundary_false_for_plain_function(self):
        func = _parse_function_def("def f():\n    return 1 + 1\n")
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertFalse(meta["side_effect_boundary"])

    def test_works_on_class_def_node_too(self):
        source = "class C:\n    def m(self):\n        pass\n"
        cls = _parse_class_def(source)
        meta = self.visitor._metadata_for_definition(cls, "C")
        self.assertEqual(meta["loc"], 3)
        self.assertTrue(meta["public_api"])

    def test_calls_nested_inside_conditional_are_still_found(self):
        # Regression guard for the BFS-via-deque traversal: calls inside an
        # `if` body must still be discovered even though the walk uses
        # iter_child_nodes rather than ast.walk.
        source = "def f():\n    if True:\n        helper()\n"
        func = _parse_function_def(source)
        meta = self.visitor._metadata_for_definition(func, "f")
        self.assertEqual(meta["dependency_count"], 1)


if __name__ == "__main__":
    unittest.main()
