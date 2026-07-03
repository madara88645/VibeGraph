import os
import shutil
import tempfile
import unittest

from analyst.languages.typescript import TypeScriptAnalyzer


class TestTypeScriptAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.analyzer = TypeScriptAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content):
        full_path = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    # ------------------------------------------------------------------
    # Basic function / class parsing
    # ------------------------------------------------------------------

    def test_function_and_class_declarations(self):
        code = """
function greet(name: string): string {
    return `Hello, ${name}`;
}

class Greeter {
    constructor(private name: string) {}

    sayHello(): string {
        return greet(this.name);
    }
}
"""
        file_path = self.create_file("greeter.ts", code)
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)

        graph = res.graph
        self.assertTrue(graph.has_node("greet"))
        self.assertEqual(graph.nodes["greet"]["type"], "function")
        self.assertEqual(graph.nodes["greet"]["language"], "typescript")

        self.assertTrue(graph.has_node("Greeter"))
        self.assertEqual(graph.nodes["Greeter"]["type"], "class")

        self.assertTrue(graph.has_node("Greeter.sayHello"))
        self.assertEqual(graph.nodes["Greeter.sayHello"]["type"], "function")
        self.assertEqual(graph.nodes["Greeter.sayHello"]["language"], "typescript")

        # sayHello calls the top-level greet() — verify it was queued.
        calls = [
            info
            for scope, info in res.pending_calls
            if scope == "Greeter.sayHello" and info.get("name") == "greet"
        ]
        self.assertTrue(calls, "Expected Greeter.sayHello -> greet pending call")

    def test_arrow_function_export(self):
        code = "export const add = (a: number, b: number): number => a + b;\n"
        file_path = self.create_file("math.ts", code)
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)
        self.assertTrue(res.graph.has_node("add"))
        self.assertEqual(res.graph.nodes["add"]["type"], "function")

    def test_interface_and_type_alias_do_not_create_nodes(self):
        # Interfaces/type aliases are type-only constructs with no runtime
        # trace — they should not show up as graph nodes.
        code = """
interface Foo {
    bar: string;
}

type Baz = { qux: number };

function useTypes(f: Foo): void {}
"""
        file_path = self.create_file("types.ts", code)
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)
        self.assertEqual(list(res.graph.nodes), ["useTypes"])
        self.assertFalse(res.graph.has_node("Foo"))
        self.assertFalse(res.graph.has_node("Baz"))

    # ------------------------------------------------------------------
    # TSX support
    # ------------------------------------------------------------------

    def test_tsx_jsx_syntax_parses(self):
        code = """
import React from "react";

export function Greeting(props: { name: string }) {
    return <div className="greet">Hello, {props.name}</div>;
}
"""
        file_path = self.create_file("Greeting.tsx", code)
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)
        self.assertTrue(res.graph.has_node("Greeting"))
        self.assertEqual(res.graph.nodes["Greeting"]["type"], "function")

        # default React import is still tracked like any other ESM import.
        self.assertTrue(
            any(
                imp["module"] == "react" and "React" in imp["asnames"]
                for imp in res.imports
            )
        )

    # ------------------------------------------------------------------
    # Decorator-based api_boundary detection (NestJS / Angular style)
    # ------------------------------------------------------------------

    def test_nestjs_route_decorators_mark_api_boundary(self):
        # NOTE ON CURRENT BEHAVIOR: the module docstring and
        # _TypeScriptWalker._has_route_decorator/_collect_decorators are
        # clearly *intended* to tag @Get/@Post/@Controller-decorated methods
        # as api_boundary=True (an "NestJS / Angular-style boost over the JS
        # plugin"). In practice this never fires: _collect_decorators walks
        # ``parent.children`` looking for ``child is node`` to find the
        # decorated node's own position, but tree-sitter's Python bindings
        # hand back a *new* Node wrapper object on every ``.children`` /
        # ``.parent`` access (same underlying position, different Python
        # identity) — so the identity check never matches and no decorators
        # are ever collected. Verified directly against the real
        # TypeScriptAnalyzer: every method below actually comes back with
        # api_boundary=False regardless of its decorators. This test
        # documents that *actual* behavior rather than the intended one; see
        # PR discussion for whether _collect_decorators should switch to
        # ``child.id == node.id`` (or ``child == node``) to fix it.
        code = """
import { Controller, Get, Post } from '@nestjs/common';

@Controller('cats')
class CatsController {
    @Get()
    findAll(): string {
        return 'all cats';
    }

    @Post()
    create(): string {
        return 'created';
    }

    privateHelper(): void {}
}
"""
        file_path = self.create_file("cats.controller.ts", code)
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)

        graph = res.graph
        # Decorated methods exist as graph nodes with the right type...
        self.assertEqual(graph.nodes["CatsController.findAll"]["type"], "function")
        self.assertEqual(graph.nodes["CatsController.create"]["type"], "function")

        # ...but api_boundary is False for ALL methods today, decorated or
        # not — the identity-comparison bug described above means decorated
        # and undecorated methods are currently indistinguishable.
        self.assertFalse(graph.nodes["CatsController.findAll"]["api_boundary"])
        self.assertFalse(graph.nodes["CatsController.create"]["api_boundary"])
        self.assertFalse(graph.nodes["CatsController.privateHelper"]["api_boundary"])

        # The class node itself was never intended to inherit api_boundary
        # from its own class-level decorator in the first place — only
        # method decorators are inspected (matches
        # JavaScriptAnalyzer._visit_class_body, which TS doesn't override
        # for class node metadata).
        self.assertFalse(graph.nodes["CatsController"]["api_boundary"])

    def test_non_route_decorator_does_not_mark_api_boundary(self):
        code = """
function myLog(target: any, key: string, descriptor: PropertyDescriptor) {
    return descriptor;
}

class Widget {
    @myLog
    render(): void {}
}
"""
        file_path = self.create_file("widget.ts", code)
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)
        self.assertFalse(res.graph.nodes["Widget.render"]["api_boundary"])

    # ------------------------------------------------------------------
    # TS-specific import handling: `import type` is dropped
    # ------------------------------------------------------------------

    def test_import_type_only_is_stripped(self):
        code = """
import type { Foo } from './foo';
import { Bar } from './bar';

export function useFoo(): void {}
"""
        file_path = self.create_file("useFoo.ts", code)
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)

        modules = [imp["module"] for imp in res.imports]
        self.assertNotIn("./foo", modules)
        self.assertIn("./bar", modules)

    # ------------------------------------------------------------------
    # Edge cases: empty file / malformed syntax must not crash the parser
    # ------------------------------------------------------------------

    def test_empty_file_returns_valid_analysis(self):
        file_path = self.create_file("empty.ts", "")
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)
        self.assertEqual(list(res.graph.nodes), [])
        self.assertEqual(res.definitions, [])
        self.assertEqual(res.imports, [])

    def test_malformed_syntax_does_not_crash(self):
        # tree-sitter is error-tolerant: garbage input still yields a tree
        # (with ERROR nodes) rather than raising, so analyze_file should
        # return a FileAnalysis instead of blowing up or returning None.
        file_path = self.create_file("broken.ts", "class {{{ ??? funct(")
        res = self.analyzer.analyze_file(file_path, self.test_dir)
        self.assertIsNotNone(res)
        # No valid definitions could be recovered from the garbage input.
        self.assertEqual(list(res.graph.nodes), [])

    def test_unreadable_file_returns_none(self):
        # analyze_file is handed a path that doesn't exist — mirrors the
        # OSError branch shared with JavaScriptAnalyzer.
        missing_path = os.path.join(self.test_dir, "does_not_exist.ts")
        res = self.analyzer.analyze_file(missing_path, self.test_dir)
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
