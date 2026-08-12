"""Direct unit coverage for analyst.analyzer's callee-classification and
call-resolution helpers, which previously had no dedicated test — only
exercised indirectly through full-file CodeAnalyzer.analyze_file
integration tests in test_analyzer.py.

_raw_callee_name / _extract_callee turn a raw ast.Call node into the info
dict later consumed by _resolve_call; _resolve_call maps that info dict to
a graph node id (and optional stub attrs) using only plain dicts/sets/
strings — no I/O. _metadata_for_definition computes per-definition graph
metadata (loc, nesting depth, dependency count, api/side-effect boundary
flags) from a function/class AST node. A bug in any of these silently
mis-wires or mis-tags the call graph without raising an error.
"""

import ast
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst.analyzer import CallGraphVisitor, CodeAnalyzer


def _parse_call(source: str) -> ast.Call:
    """Parse a one-line expression statement like 'foo()' and return its Call node."""
    module = ast.parse(source)
    stmt = module.body[0]
    assert isinstance(stmt, ast.Expr)
    assert isinstance(stmt.value, ast.Call)
    return stmt.value


def _parse_def(source: str) -> ast.FunctionDef | ast.ClassDef:
    module = ast.parse(source)
    node = module.body[0]
    assert isinstance(node, (ast.FunctionDef, ast.ClassDef))
    return node


class TestRawCalleeName(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_bare_name_call(self):
        node = _parse_call("foo()")
        self.assertEqual(self.visitor._raw_callee_name(node), "foo")

    def test_attribute_call_returns_rightmost_attr(self):
        node = _parse_call("obj.method()")
        self.assertEqual(self.visitor._raw_callee_name(node), "method")

    def test_deep_attribute_chain_returns_rightmost_attr(self):
        node = _parse_call("a.b.c.deep_method()")
        self.assertEqual(self.visitor._raw_callee_name(node), "deep_method")

    def test_chained_call_result_returns_none(self):
        # foo()() -> node.func is a Call, not Name/Attribute
        node = _parse_call("foo()()")
        self.assertIsNone(self.visitor._raw_callee_name(node))


class TestExtractCallee(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_bare_name_call(self):
        node = _parse_call("foo()")
        self.assertEqual(self.visitor._extract_callee(node), {"kind": "name", "name": "foo"})

    def test_self_method_call_inside_class_body(self):
        self.visitor.class_stack.append("MyClass")
        node = _parse_call("self.helper()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "self_method", "name": "helper", "class": "MyClass"},
        )

    def test_cls_method_call_inside_class_body(self):
        self.visitor.class_stack.append("MyClass")
        node = _parse_call("cls.helper()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "self_method", "name": "helper", "class": "MyClass"},
        )

    def test_self_call_outside_class_body_is_attribute_not_self_method(self):
        # No class_stack entry -> `self` is treated as an ordinary base name.
        node = _parse_call("self.helper()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "attribute", "name": "helper", "base": "self", "parts": ["helper"]},
        )

    def test_simple_attribute_call(self):
        node = _parse_call("obj.method()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "attribute", "name": "method", "base": "obj", "parts": ["method"]},
        )

    def test_deep_attribute_chain_records_full_parts(self):
        node = _parse_call("a.b.c.deep_method()")
        self.assertEqual(
            self.visitor._extract_callee(node),
            {"kind": "attribute", "name": "deep_method", "base": "a", "parts": ["b", "c", "deep_method"]},
        )

    def test_chained_call_result_returns_none(self):
        node = _parse_call("foo()()")
        self.assertIsNone(self.visitor._extract_callee(node))

    def test_subscript_target_returns_none(self):
        node = _parse_call("handlers[0]()")
        self.assertIsNone(self.visitor._extract_callee(node))


class TestMetadataForDefinition(unittest.TestCase):
    def setUp(self):
        self.visitor = CallGraphVisitor("test.py")

    def test_simple_function_is_public_with_no_dependencies(self):
        node = _parse_def("def foo():\n    return 1\n")
        meta = self.visitor._metadata_for_definition(node, "foo")
        self.assertTrue(meta["public_api"])
        self.assertFalse(meta["api_boundary"])
        self.assertFalse(meta["side_effect_boundary"])
        self.assertEqual(meta["dependency_count"], 0)
        self.assertEqual(meta["nesting_depth"], 0)
        self.assertEqual(meta["loc"], 2)

    def test_private_name_is_not_public_api(self):
        node = _parse_def("def _helper():\n    return 1\n")
        meta = self.visitor._metadata_for_definition(node, "_helper")
        self.assertFalse(meta["public_api"])

    def test_qualified_private_name_checks_last_segment_only(self):
        node = _parse_def("def _helper():\n    return 1\n")
        meta = self.visitor._metadata_for_definition(node, "MyClass._helper")
        self.assertFalse(meta["public_api"])

    def test_route_decorator_marks_api_boundary(self):
        node = _parse_def('@app.get("/x")\ndef handler():\n    return 1\n')
        meta = self.visitor._metadata_for_definition(node, "handler")
        self.assertTrue(meta["api_boundary"])
        self.assertTrue(meta["side_effect_boundary"])

    def test_side_effect_module_import_marks_side_effect_boundary(self):
        node = _parse_def("def foo():\n    import os\n    return os.getcwd()\n")
        meta = self.visitor._metadata_for_definition(node, "foo")
        self.assertTrue(meta["side_effect_boundary"])
        self.assertFalse(meta["api_boundary"])

    def test_side_effect_call_name_marks_side_effect_boundary(self):
        node = _parse_def("def foo(f):\n    f.write('x')\n")
        meta = self.visitor._metadata_for_definition(node, "foo")
        self.assertTrue(meta["side_effect_boundary"])

    def test_dependency_count_counts_distinct_call_names(self):
        node = _parse_def("def foo():\n    bar()\n    baz()\n    bar()\n")
        meta = self.visitor._metadata_for_definition(node, "foo")
        self.assertEqual(meta["dependency_count"], 2)

    def test_nesting_depth_reflects_control_flow_depth(self):
        node = _parse_def(
            "def foo():\n"
            "    if True:\n"
            "        for x in range(1):\n"
            "            pass\n"
        )
        meta = self.visitor._metadata_for_definition(node, "foo")
        self.assertEqual(meta["nesting_depth"], 2)


class TestResolveCall(unittest.TestCase):
    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_self_method_resolves_to_local_definition(self):
        info = {"kind": "self_method", "name": "helper", "class": "MyClass"}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids={"MyClass.helper"},
        )
        self.assertEqual(target, "MyClass.helper")
        self.assertIsNone(attrs)

    def test_self_method_falls_back_to_unresolved_stub(self):
        info = {"kind": "self_method", "name": "helper", "class": "MyClass"}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids=set(),
        )
        self.assertEqual(target, "unresolved:MyClass.helper")
        self.assertEqual(attrs["type"], "unresolved")

    def test_name_resolves_to_local_definition(self):
        info = {"kind": "name", "name": "foo"}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids={"foo"},
        )
        self.assertEqual(target, "foo")
        self.assertIsNone(attrs)

    def test_name_resolves_to_builtin(self):
        info = {"kind": "name", "name": "len"}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids=set(),
            builtins=frozenset({"len"}),
        )
        self.assertEqual(target, "builtin:len")
        self.assertEqual(attrs["type"], "builtin")

    def test_name_resolves_via_local_from_import(self):
        info = {"kind": "name", "name": "helper"}
        imports = [{
            "kind": "from", "module": "pkg", "names": ["helper"],
            "asnames": ["helper"], "is_local": True, "level": 0,
        }]
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=imports, symbol_table={"helper": "pkg.helper"},
            local_modules=frozenset(), local_def_ids=set(), builtins=frozenset(),
        )
        self.assertEqual(target, "pkg.helper")
        self.assertIsNone(attrs)

    def test_name_resolves_via_external_from_import(self):
        info = {"kind": "name", "name": "loads"}
        imports = [{
            "kind": "from", "module": "json", "names": ["loads"],
            "asnames": ["loads"], "is_local": False, "level": 0,
        }]
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=imports, symbol_table={},
            local_modules=frozenset(), local_def_ids=set(), builtins=frozenset(),
        )
        self.assertEqual(target, "external:json.loads")
        self.assertEqual(attrs["type"], "external")

    def test_name_final_fallthrough_is_unresolved(self):
        info = {"kind": "name", "name": "mystery"}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids=set(), builtins=frozenset(),
        )
        self.assertEqual(target, "unresolved:mystery")
        self.assertEqual(attrs["type"], "unresolved")

    def test_attribute_resolves_via_stdlib_module_base(self):
        info = {"kind": "attribute", "name": "exists", "base": "os", "parts": ["path", "exists"]}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids=set(),
            stdlib_modules=frozenset({"os"}),
        )
        self.assertEqual(target, "external:os.path.exists")
        self.assertEqual(attrs["module"], "os")

    def test_attribute_falls_back_to_unresolved_when_base_unknown(self):
        info = {"kind": "attribute", "name": "run", "base": "mystery_obj", "parts": ["run"]}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids=set(), stdlib_modules=frozenset(),
        )
        self.assertEqual(target, "unresolved:run")
        self.assertEqual(attrs["type"], "unresolved")

    def test_unknown_kind_defaults_to_unresolved(self):
        info = {"kind": "subscript", "name": "weird"}
        target, attrs = self.analyzer._resolve_call(
            info, "f.py", imports=[], symbol_table={},
            local_modules=frozenset(), local_def_ids=set(),
        )
        self.assertEqual(target, "unresolved:weird")
        self.assertEqual(attrs["type"], "unresolved")


if __name__ == "__main__":
    unittest.main()
