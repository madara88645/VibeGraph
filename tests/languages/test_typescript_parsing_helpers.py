"""Direct unit coverage for analyst.languages.typescript private AST helpers
that previously had no dedicated test — only exercised indirectly through
full-file TypeScriptAnalyzer.analyze_file fixture tests in test_typescript.py.

_TypeScriptWalker._dotted_text resolves a TS identifier / member-expression
AST node into a dotted string (e.g. ``a.b.c``) — it feeds decorator-name
resolution used for API-boundary tagging. _decorator_name unwraps a
``decorator`` node (optionally call-wrapped, e.g. ``@Get('/x')``) down to
its dotted name. _collect_decorators walks the preceding siblings of a
declaration node to gather the ``decorator`` nodes that apply to it. A bug
in any of these silently drops or mis-resolves NestJS/Angular-style route
decorators without raising an error, mirroring the gap already backfilled
for the JS analyzer in test_javascript_parsing_helpers.py.
"""

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analyst.languages.typescript import _TypeScriptWalker
from analyst.tree_sitter_loader import get_parser


def _parse(source: str):
    parser = get_parser("typescript")
    return parser.parse(source.encode("utf-8"))


def _find_first(node, node_type: str):
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == node_type:
            return current
        stack.extend(reversed(current.children))
    return None


def _find_all(node, node_type: str):
    out = []
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == node_type:
            out.append(current)
        stack.extend(reversed(current.children))
    return out


def _walker(source: str) -> _TypeScriptWalker:
    return _TypeScriptWalker(
        file_path="<test>", source=source.encode("utf-8"), language_id="typescript"
    )


class TestDottedText(unittest.TestCase):
    def test_plain_identifier(self):
        source = "Get();"
        tree = _parse(source)
        node = _find_first(tree.root_node, "identifier")
        self.assertEqual(_walker(source)._dotted_text(node), "Get")

    def test_single_level_member_expression(self):
        source = "a.b;"
        tree = _parse(source)
        node = _find_first(tree.root_node, "member_expression")
        self.assertEqual(_walker(source)._dotted_text(node), "a.b")

    def test_nested_member_expression(self):
        source = "a.b.c.d;"
        tree = _parse(source)
        node = _find_first(tree.root_node, "member_expression")
        self.assertEqual(_walker(source)._dotted_text(node), "a.b.c.d")

    def test_non_identifier_non_member_falls_back_to_raw_text(self):
        # A call expression node isn't identifier/member_expression, so the
        # fallback branch (raw source text) is exercised.
        source = "foo();"
        tree = _parse(source)
        node = _find_first(tree.root_node, "call_expression")
        self.assertEqual(_walker(source)._dotted_text(node), "foo()")


class TestDecoratorName(unittest.TestCase):
    def _decorator_node(self, source: str):
        tree = _parse(source)
        return _find_first(tree.root_node, "decorator")

    def test_plain_decorator_no_call(self):
        source = "class X { @Injectable m() {} }"
        node = self._decorator_node(source)
        self.assertEqual(_walker(source)._decorator_name(node), "Injectable")

    def test_call_wrapped_decorator(self):
        source = "class X { @Get('/x') m() {} }"
        node = self._decorator_node(source)
        self.assertEqual(_walker(source)._decorator_name(node), "Get")

    def test_call_wrapped_decorator_no_args(self):
        source = "class X { @Controller() m() {} }"
        node = self._decorator_node(source)
        self.assertEqual(_walker(source)._decorator_name(node), "Controller")

    def test_dotted_call_wrapped_decorator(self):
        source = "class X { @Module.Get('/x') m() {} }"
        node = self._decorator_node(source)
        self.assertEqual(_walker(source)._decorator_name(node), "Module.Get")

    def test_dotted_non_call_decorator(self):
        source = "class X { @Module.Injectable m() {} }"
        node = self._decorator_node(source)
        self.assertEqual(_walker(source)._decorator_name(node), "Module.Injectable")


class TestCollectDecorators(unittest.TestCase):
    def test_single_method_decorator(self):
        source = "class X { @Get('/x') m() {} }"
        tree = _parse(source)
        method = _find_first(tree.root_node, "method_definition")
        decs = _walker(source)._collect_decorators(method)
        self.assertEqual(len(decs), 1)
        self.assertEqual(decs[0].type, "decorator")

    def test_multiple_stacked_decorators(self):
        source = "class X { @Get('/x') @UseGuards(AuthGuard) m() {} }"
        tree = _parse(source)
        method = _find_first(tree.root_node, "method_definition")
        decs = _walker(source)._collect_decorators(method)
        self.assertEqual(len(decs), 2)

    def test_no_decorators_returns_empty_list(self):
        source = "class X { m() {} }"
        tree = _parse(source)
        method = _find_first(tree.root_node, "method_definition")
        decs = _walker(source)._collect_decorators(method)
        self.assertEqual(decs, [])

    def test_class_level_decorator_is_not_found_via_sibling_walk(self):
        # tree-sitter-typescript nests a class-level decorator *inside* the
        # class_declaration node (as its first child) rather than as a
        # preceding sibling in `program` — unlike method decorators, which
        # really are preceding siblings inside class_body. So calling
        # _collect_decorators directly on a class_declaration node finds
        # nothing, which matches the documented real-world behaviour that
        # only method decorators are inspected for api_boundary tagging
        # (see test_typescript.py::test_nestjs_route_decorators_mark_api_boundary).
        source = "@Controller('/x') class X { m() {} }"
        tree = _parse(source)
        cls = _find_first(tree.root_node, "class_declaration")
        decs = _walker(source)._collect_decorators(cls)
        self.assertEqual(decs, [])

    def test_decorator_on_second_method_does_not_leak_to_first(self):
        # Ensure siblings are scanned only up to the first non-decorator,
        # non-comment sibling — a decorator on a *different* method must not
        # attach to an undecorated one.
        source = "class X { a() {} @Get('/x') b() {} }"
        tree = _parse(source)
        methods = _find_all(tree.root_node, "method_definition")
        walker = _walker(source)
        # methods[0] is `a`, methods[1] is `b`
        first_method_name = walker._text(methods[0].child_by_field_name("name"))
        second_method_name = walker._text(methods[1].child_by_field_name("name"))
        self.assertEqual(first_method_name, "a")
        self.assertEqual(second_method_name, "b")
        self.assertEqual(walker._collect_decorators(methods[0]), [])
        self.assertEqual(len(walker._collect_decorators(methods[1])), 1)

    def test_root_node_with_no_parent_returns_empty_list(self):
        source = "class X {}"
        tree = _parse(source)
        decs = _walker(source)._collect_decorators(tree.root_node)
        self.assertEqual(decs, [])


if __name__ == "__main__":
    unittest.main()
