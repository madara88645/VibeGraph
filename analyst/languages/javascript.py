"""JavaScript language plugin (tree-sitter).

Parses ``.js / .jsx / .mjs / .cjs`` files and emits the same ``FileAnalysis``
shape that the Python plugin emits, so the orchestrator's two-pass call
resolver and graph composition stay language-agnostic.

The plugin recognises:
  * ``function`` and ``function*`` declarations
  * Arrow functions / function expressions assigned to a top-level binding
  * ``class`` declarations with ``method_definition`` members
  * Class fields whose value is an arrow function or function expression
  * ESM ``import`` statements (default, named, namespace)
  * ``require("…")`` bound to a const/let/var (single or destructured)
  * Calls — bare names, member expressions, and ``this.method()``

It deliberately does *not* try to do dataflow (e.g. ``app.get('/x', h)`` →
route registration). That's a future enhancement gated on parity tests.
"""

from __future__ import annotations

import os
import time
from typing import Any

import networkx as nx

from analyst.languages.base import FileAnalysis
from analyst.tree_sitter_loader import get_parser

# ECMAScript globals + browser/Node globals that show up unqualified in
# everyday code. The list is intentionally broad — false positives here are
# cheap (a node tagged ``builtin`` instead of ``unresolved``), false
# negatives leave the graph noisy.
_JS_BUILTINS: frozenset[str] = frozenset(
    {
        "Array",
        "ArrayBuffer",
        "Boolean",
        "DataView",
        "Date",
        "Error",
        "EvalError",
        "Float32Array",
        "Float64Array",
        "Function",
        "Generator",
        "GeneratorFunction",
        "Infinity",
        "Int8Array",
        "Int16Array",
        "Int32Array",
        "JSON",
        "Map",
        "Math",
        "NaN",
        "Number",
        "Object",
        "Promise",
        "Proxy",
        "RangeError",
        "ReferenceError",
        "Reflect",
        "RegExp",
        "Set",
        "SharedArrayBuffer",
        "String",
        "Symbol",
        "SyntaxError",
        "TypeError",
        "URIError",
        "Uint8Array",
        "Uint8ClampedArray",
        "Uint16Array",
        "Uint32Array",
        "WeakMap",
        "WeakRef",
        "WeakSet",
        "decodeURI",
        "decodeURIComponent",
        "encodeURI",
        "encodeURIComponent",
        "eval",
        "globalThis",
        "isFinite",
        "isNaN",
        "parseFloat",
        "parseInt",
        "undefined",
        # Console / timers / fetch
        "console",
        "setTimeout",
        "setInterval",
        "clearTimeout",
        "clearInterval",
        "queueMicrotask",
        "structuredClone",
        "fetch",
        "AbortController",
        "AbortSignal",
        "URL",
        "URLSearchParams",
        # Browser globals
        "window",
        "document",
        "navigator",
        "location",
        "history",
        "localStorage",
        "sessionStorage",
        "alert",
        "confirm",
        "prompt",
        # Node-specific globals
        "process",
        "Buffer",
        "global",
        "require",
        "module",
        "exports",
        "__dirname",
        "__filename",
    }
)


_NODE_STDLIB_BARE: frozenset[str] = frozenset(
    {
        "assert",
        "async_hooks",
        "buffer",
        "child_process",
        "cluster",
        "console",
        "crypto",
        "dgram",
        "diagnostics_channel",
        "dns",
        "events",
        "fs",
        "http",
        "http2",
        "https",
        "inspector",
        "module",
        "net",
        "os",
        "path",
        "perf_hooks",
        "process",
        "querystring",
        "readline",
        "stream",
        "string_decoder",
        "test",
        "timers",
        "tls",
        "trace_events",
        "tty",
        "url",
        "util",
        "v8",
        "vm",
        "wasi",
        "worker_threads",
        "zlib",
    }
)
_NODE_STDLIB: frozenset[str] = _NODE_STDLIB_BARE | frozenset(
    f"node:{m}" for m in _NODE_STDLIB_BARE
)


_JS_SIDE_EFFECT_CALLS: frozenset[str] = frozenset(
    {
        "fetch",
        "open",
        "readFile",
        "readFileSync",
        "writeFile",
        "writeFileSync",
        "appendFile",
        "appendFileSync",
        "unlink",
        "unlinkSync",
        "rm",
        "rmSync",
        "rename",
        "renameSync",
        "exec",
        "execSync",
        "spawn",
        "spawnSync",
        "fork",
        "request",
        "send",
        "query",
        "execute",
    }
)
_JS_SIDE_EFFECT_MODULES: frozenset[str] = frozenset(
    {
        "fs",
        "fs/promises",
        "http",
        "https",
        "net",
        "child_process",
        "dgram",
        "tls",
        "node:fs",
        "node:fs/promises",
        "node:http",
        "node:https",
        "node:net",
        "node:child_process",
        "node:dgram",
        "node:tls",
    }
)


_JS_NESTING_NODES: frozenset[str] = frozenset(
    {
        "if_statement",
        "for_statement",
        "for_in_statement",
        "for_of_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
        "try_statement",
        "with_statement",
    }
)


_JS_IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        ".next",
        ".nuxt",
        "dist",
        "build",
        "out",
        "coverage",
        ".turbo",
        ".cache",
    }
)


_FUNCTION_BODY_NODES: frozenset[str] = frozenset(
    {
        "function_declaration",
        "generator_function_declaration",
        "function_expression",
        "function",
        "arrow_function",
        "method_definition",
        "class_declaration",
        "class_expression",
    }
)


class JavaScriptAnalyzer:
    language_id = "javascript"
    display_label = "JavaScript"
    extensions: tuple[str, ...] = (".js", ".jsx", ".mjs", ".cjs")
    _ts_language_name: str = "javascript"

    @property
    def builtins(self) -> frozenset[str]:
        return _JS_BUILTINS

    @property
    def stdlib_modules(self) -> frozenset[str]:
        return _NODE_STDLIB

    def get_local_modules(self, project_root: str) -> frozenset[str]:
        """Walk the project tree and return dotted module ids for every
        source file the plugin recognises. ``index`` files are dropped
        (paralleling Python's ``__init__`` skip).
        """
        local: set[str] = set()
        stack: list[tuple[str, list[str]]] = [(project_root, [])]
        ext_set = set(ext.lower() for ext in self.extensions)
        while stack:
            current_dir, parts = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name in _JS_IGNORED_DIRS:
                                continue
                            new_parts = parts + [entry.name]
                            local.add(".".join(new_parts))
                            stack.append((entry.path, new_parts))
                        elif entry.is_file(follow_symlinks=False):
                            base, ext = os.path.splitext(entry.name)
                            if ext.lower() in ext_set:
                                if base == "index":
                                    continue
                                local.add(".".join(parts + [base]))
            except OSError:
                continue
        return frozenset(local)

    def module_id_from_path(self, file_path: str, project_root: str | None) -> str:
        if project_root:
            try:
                rel = os.path.relpath(file_path, project_root)
            except ValueError:
                rel = os.path.basename(file_path)
        else:
            rel = os.path.basename(file_path)
        rel = rel.replace(os.sep, "/")
        for ext in self.extensions:
            if rel.lower().endswith(ext):
                rel = rel[: -len(ext)]
                break
        if rel.endswith("/index"):
            rel = rel[: -len("/index")]
        return rel.replace("/", ".") or os.path.basename(file_path)

    def analyze_file(
        self,
        file_path: str,
        project_root: str | None,
        local_modules_override: frozenset[str] | None = None,
        profile_bucket: dict[str, Any] | None = None,
    ) -> FileAnalysis | None:
        try:
            with open(file_path, "rb") as f:
                source = f.read()
        except (UnicodeDecodeError, ValueError, OSError):
            return None

        t_parse = time.perf_counter() if profile_bucket is not None else 0.0
        try:
            parser = get_parser(self._ts_language_name)
            tree = parser.parse(source)
        except Exception:
            return None
        if tree is None or tree.root_node is None:
            return None
        if profile_bucket is not None:
            profile_bucket["tree_sitter_parse_ms"] = profile_bucket.get(
                "tree_sitter_parse_ms", 0.0
            ) + (time.perf_counter() - t_parse) * 1000

        scan_root = project_root or os.path.dirname(os.path.abspath(file_path))
        t_modules = time.perf_counter() if profile_bucket is not None else 0.0
        local_modules = local_modules_override
        if local_modules is None:
            local_modules = self.get_local_modules(scan_root)
            if profile_bucket is not None:
                profile_bucket["local_modules_scan_count"] = profile_bucket.get(
                    "local_modules_scan_count", 0
                ) + 1
        if profile_bucket is not None:
            profile_bucket["local_modules_lookup_ms"] = profile_bucket.get(
                "local_modules_lookup_ms", 0.0
            ) + (time.perf_counter() - t_modules) * 1000

        t_walk = time.perf_counter() if profile_bucket is not None else 0.0
        walker = _Walker(
            file_path=file_path,
            source=source,
            language_id=self.language_id,
        )
        walker.walk_module(tree.root_node)
        imports = _extract_imports(tree.root_node, source, local_modules)
        if profile_bucket is not None:
            profile_bucket["walker_ms"] = profile_bucket.get("walker_ms", 0.0) + (
                time.perf_counter() - t_walk
            ) * 1000

        return FileAnalysis(
            file_path=file_path,
            graph=walker.graph,
            top_level_definitions=list(walker.top_level_definitions),
            definitions=list(walker.definitions),
            pending_calls=list(walker.pending_calls),
            imports=imports,
        )


# ---------------------------------------------------------------------------
# Walker — collects definitions and queues calls for the orchestrator
# ---------------------------------------------------------------------------


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _strip_string_quotes(raw: str) -> str:
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] in ("'", '"', "`") and raw[-1] == raw[0]:
        return raw[1:-1]
    return raw


class _Walker:
    def __init__(self, file_path: str, source: bytes, language_id: str):
        self.file_path = file_path
        self.source = source
        self.language_id = language_id
        self.graph: nx.DiGraph = nx.DiGraph()
        self.current_scope = "global"
        self.class_stack: list[str] = []
        self.definitions: list[dict[str, Any]] = []
        self.top_level_definitions: list[dict[str, Any]] = []
        self.pending_calls: list[tuple[str, dict[str, Any]]] = []

    # --- text/position helpers ---

    def _text(self, node) -> str:
        return _node_text(node, self.source)

    def _lineno(self, node) -> int:
        return node.start_point[0] + 1

    def _end_lineno(self, node) -> int:
        return node.end_point[0] + 1

    # --- top-level traversal ---

    def walk_module(self, root) -> None:
        for child in root.children:
            self._visit_top_level(child)

    def _visit_top_level(self, node) -> None:
        if node.type == "export_statement":
            inner = node.child_by_field_name("declaration")
            if inner is not None:
                self._visit_top_level(inner)
                return
            # `export { a, b }` / `export default expr` — still scan for calls
            self._collect_calls(node, scope="global")
            return

        if node.type in ("function_declaration", "generator_function_declaration"):
            self._visit_function_declaration(node, is_top_level=True)
            return
        if node.type == "class_declaration":
            self._visit_class_declaration(node, is_top_level=True)
            return
        if node.type in ("lexical_declaration", "variable_declaration"):
            for declarator in node.children:
                if declarator.type == "variable_declarator":
                    self._visit_top_level_declarator(declarator)
            return

        # Other top-level statements: still queue any calls they make at the
        # module ("global") scope so things like `app.use(...)` show up.
        self._collect_calls(node, scope="global")

    def _visit_top_level_declarator(self, declarator) -> None:
        name_node = declarator.child_by_field_name("name")
        value_node = declarator.child_by_field_name("value")
        if value_node is None:
            return
        if name_node is not None and name_node.type == "identifier":
            name = self._text(name_node)
            if value_node.type in (
                "arrow_function",
                "function_expression",
                "function",
            ):
                self._visit_function_value(
                    value_node,
                    name=name,
                    is_top_level=True,
                    decl_lineno=self._lineno(declarator),
                )
                return
            if value_node.type in ("class_expression", "class"):
                self._visit_class_expression(
                    value_node, class_name=name, is_top_level=True
                )
                return
        # Not a function/class binding — still scan the initialiser for calls.
        self._collect_calls(value_node, scope="global")

    # --- function / class visitors ---

    def _visit_function_declaration(self, node, is_top_level: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = self._text(name_node)
        full_name = self._qualify(name)
        self._add_function_node(
            full_name,
            node,
            short_name=name,
            is_top_level=is_top_level,
        )
        body = node.child_by_field_name("body")
        if body is not None:
            previous = self.current_scope
            self.current_scope = full_name
            self._collect_calls(body, scope=full_name)
            self._walk_nested(body)
            self.current_scope = previous

    def _visit_function_value(
        self, node, name: str, is_top_level: bool, decl_lineno: int
    ) -> None:
        full_name = self._qualify(name)
        self._add_function_node(
            full_name,
            node,
            short_name=name,
            is_top_level=is_top_level,
            override_lineno=decl_lineno,
        )
        body = node.child_by_field_name("body")
        if body is not None:
            previous = self.current_scope
            self.current_scope = full_name
            self._collect_calls(body, scope=full_name)
            self._walk_nested(body)
            self.current_scope = previous

    def _visit_class_declaration(self, node, is_top_level: bool) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        class_name = self._text(name_node)
        self._visit_class_body(node, class_name=class_name, is_top_level=is_top_level)

    def _visit_class_expression(
        self, node, class_name: str, is_top_level: bool
    ) -> None:
        self._visit_class_body(node, class_name=class_name, is_top_level=is_top_level)

    def _visit_class_body(self, node, class_name: str, is_top_level: bool) -> None:
        end_lineno = self._end_lineno(node)
        lineno = self._lineno(node)
        self.graph.add_node(
            class_name,
            type="class",
            lineno=lineno,
            docstring=None,
            file=self.file_path,
            entry_point=False,
            language=self.language_id,
            end_lineno=end_lineno,
            loc=max(end_lineno - lineno + 1, 1),
            nesting_depth=0,
            dependency_count=0,
            public_api=not class_name.startswith("_"),
            api_boundary=False,
            side_effect_boundary=False,
        )
        record = {"name": class_name, "type": "class", "lineno": lineno}
        self.definitions.append(record)
        if is_top_level:
            self.top_level_definitions.append(record)

        body = node.child_by_field_name("body")
        if body is None:
            return
        self.class_stack.append(class_name)
        try:
            for child in body.children:
                if child.type == "method_definition":
                    self._visit_method_definition(child, class_name=class_name)
                elif child.type in ("field_definition", "public_field_definition"):
                    self._visit_field_definition(child, class_name=class_name)
        finally:
            self.class_stack.pop()

    def _visit_method_definition(self, node, class_name: str) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        method_name = self._text(name_node)
        full_name = f"{class_name}.{method_name}"
        self._add_function_node(
            full_name, node, short_name=method_name, is_top_level=False
        )
        body = node.child_by_field_name("body")
        if body is not None:
            previous = self.current_scope
            self.current_scope = full_name
            self._collect_calls(body, scope=full_name)
            self._walk_nested(body)
            self.current_scope = previous

    def _visit_field_definition(self, node, class_name: str) -> None:
        # `myField = () => …` / `myField = function() …`
        name_node = node.child_by_field_name("property") or node.child_by_field_name(
            "name"
        )
        value_node = node.child_by_field_name("value")
        if (
            name_node is None
            or value_node is None
            or value_node.type
            not in ("arrow_function", "function_expression", "function")
        ):
            return
        method_name = self._text(name_node)
        full_name = f"{class_name}.{method_name}"
        self._add_function_node(
            full_name, value_node, short_name=method_name, is_top_level=False
        )
        body = value_node.child_by_field_name("body")
        if body is not None:
            previous = self.current_scope
            self.current_scope = full_name
            self._collect_calls(body, scope=full_name)
            self._walk_nested(body)
            self.current_scope = previous

    def _walk_nested(self, body) -> None:
        """Discover nested function/class declarations inside a function body
        so they become their own graph nodes (matches Python's recursive
        ``ast.NodeVisitor`` behaviour)."""
        stack = list(body.children)
        while stack:
            n = stack.pop()
            if n.type in ("function_declaration", "generator_function_declaration"):
                self._visit_function_declaration(n, is_top_level=False)
                continue
            if n.type == "class_declaration":
                self._visit_class_declaration(n, is_top_level=False)
                continue
            if n.type in ("lexical_declaration", "variable_declaration"):
                for d in n.children:
                    if d.type == "variable_declarator":
                        nm = d.child_by_field_name("name")
                        val = d.child_by_field_name("value")
                        if (
                            nm is not None
                            and val is not None
                            and nm.type == "identifier"
                            and val.type
                            in ("arrow_function", "function_expression", "function")
                        ):
                            self._visit_function_value(
                                val,
                                name=self._text(nm),
                                is_top_level=False,
                                decl_lineno=self._lineno(d),
                            )
                continue
            # Don't descend into another function's body — its own visitor
            # already collected the definitions inside it.
            if n.type in _FUNCTION_BODY_NODES:
                continue
            stack.extend(n.children)

    # --- node-creation + metadata ---

    def _qualify(self, name: str) -> str:
        if self.current_scope != "global" and not self.current_scope.endswith(
            "<module>"
        ):
            return f"{self.current_scope}.{name}"
        return name

    def _add_function_node(
        self,
        full_name: str,
        node,
        short_name: str,
        is_top_level: bool,
        override_lineno: int | None = None,
    ) -> None:
        lineno = override_lineno if override_lineno is not None else self._lineno(node)
        end_lineno = self._end_lineno(node)
        body = node.child_by_field_name("body")
        nesting_depth = self._max_nesting_depth(body) if body is not None else 0
        calls, side_effect_imports = (
            self._collect_immediate_metadata(body)
            if body is not None
            else (set(), False)
        )
        api_boundary = self._has_route_decorator(node)
        side_effect_boundary = (
            api_boundary or side_effect_imports or bool(calls & _JS_SIDE_EFFECT_CALLS)
        )
        is_entry = short_name in {"main", "init", "start", "run", "app"} or is_top_level

        self.graph.add_node(
            full_name,
            type="function",
            lineno=lineno,
            docstring=None,
            file=self.file_path,
            entry_point=is_entry,
            language=self.language_id,
            end_lineno=end_lineno,
            loc=max(end_lineno - lineno + 1, 1),
            nesting_depth=nesting_depth,
            dependency_count=len(calls),
            public_api=not short_name.startswith("_"),
            api_boundary=api_boundary,
            side_effect_boundary=side_effect_boundary,
        )
        record = {"name": full_name, "type": "function", "lineno": lineno}
        self.definitions.append(record)
        if is_top_level:
            self.top_level_definitions.append(record)

    def _max_nesting_depth(self, node) -> int:
        max_depth = 0
        stack: list[tuple[Any, int]] = [(node, 0)]
        while stack:
            current, depth = stack.pop()
            next_depth = depth + 1 if current.type in _JS_NESTING_NODES else depth
            if next_depth > max_depth:
                max_depth = next_depth
            for child in current.children:
                stack.append((child, next_depth))
        return max_depth

    def _collect_immediate_metadata(self, body) -> tuple[set[str], bool]:
        """Collect the set of call short-names AND whether the body imports a
        side-effect module (via ``require`` or top-level ``import``). Used
        only for per-definition metadata (``dependency_count``,
        ``side_effect_boundary``); the orchestrator sees the queued
        ``pending_calls`` separately.
        """
        calls: set[str] = set()
        side_effect = False
        stack = [body]
        while stack:
            n = stack.pop()
            if n.type == "call_expression":
                func = n.child_by_field_name("function")
                if func is not None:
                    if func.type == "identifier":
                        nm = self._text(func)
                        calls.add(nm)
                        if nm == "require":
                            args = n.child_by_field_name("arguments")
                            if args is not None:
                                for arg in args.children:
                                    if arg.type == "string":
                                        s = _strip_string_quotes(self._text(arg))
                                        if s in _JS_SIDE_EFFECT_MODULES:
                                            side_effect = True
                    elif func.type == "member_expression":
                        prop = func.child_by_field_name("property")
                        if prop is not None and prop.type == "property_identifier":
                            calls.add(self._text(prop))
            elif n.type == "import_statement":
                src = n.child_by_field_name("source")
                if src is not None and src.type == "string":
                    s = _strip_string_quotes(self._text(src))
                    if s in _JS_SIDE_EFFECT_MODULES:
                        side_effect = True
            for c in n.children:
                stack.append(c)
        return calls, side_effect

    def _has_route_decorator(self, node) -> bool:
        # Pure JS doesn't have decorators — TypeScript subclass overrides.
        return False

    # --- call queueing ---

    def _collect_calls(self, body, scope: str) -> None:
        stack = [body]
        while stack:
            n = stack.pop()
            if n.type == "call_expression":
                info = self._classify_call(n)
                if info is not None:
                    info["lineno"] = self._lineno(n)
                    self.pending_calls.append((scope, info))
                # Continue into arguments — calls nest.
                for c in n.children:
                    stack.append(c)
                continue
            # Don't descend into another function/class body — handled by its
            # own visitor with the right scope.
            if n.type in _FUNCTION_BODY_NODES:
                continue
            for c in n.children:
                stack.append(c)

    def _classify_call(self, call_node) -> dict[str, Any] | None:
        func = call_node.child_by_field_name("function")
        if func is None:
            return None
        if func.type == "identifier":
            return {"kind": "name", "name": self._text(func)}
        if func.type == "member_expression":
            parts: list[str] = []
            cur = func
            while cur is not None and cur.type == "member_expression":
                prop = cur.child_by_field_name("property")
                if prop is not None:
                    parts.insert(0, self._text(prop))
                cur = cur.child_by_field_name("object")
            attr_name = parts[-1] if parts else ""
            if cur is not None and cur.type == "identifier":
                base = self._text(cur)
                if base == "this" and len(parts) == 1 and self.class_stack:
                    return {
                        "kind": "self_method",
                        "name": attr_name,
                        "class": self.class_stack[-1],
                    }
                return {
                    "kind": "attribute",
                    "name": attr_name,
                    "base": base,
                    "parts": parts,
                }
            if (
                cur is not None
                and cur.type == "this"
                and len(parts) == 1
                and self.class_stack
            ):
                return {
                    "kind": "self_method",
                    "name": attr_name,
                    "class": self.class_stack[-1],
                }
            if attr_name:
                return {
                    "kind": "attribute",
                    "name": attr_name,
                    "base": None,
                    "parts": parts,
                }
        return None


# ---------------------------------------------------------------------------
# Import extraction
# ---------------------------------------------------------------------------


def _extract_imports(
    root, source: bytes, local_modules: frozenset[str]
) -> list[dict[str, Any]]:
    """Walk the tree and emit Python-shaped import records for ESM
    ``import_statement`` nodes and ``require()`` bindings."""
    out: list[dict[str, Any]] = []
    stack = [root]
    while stack:
        n = stack.pop()
        if n.type == "import_statement":
            entries = _parse_import_statement(n, source, local_modules)
            out.extend(entries)
            # Don't descend — handled.
            continue
        if n.type == "call_expression":
            entry = _parse_require_call(n, source, local_modules)
            if entry is not None:
                out.append(entry)
        for c in n.children:
            stack.append(c)
    return out


def _is_local_module(module_path: str, local_modules: frozenset[str]) -> bool:
    if (
        module_path.startswith("./")
        or module_path.startswith("../")
        or module_path.startswith("/")
    ):
        return True
    top = module_path.split("/")[0]
    return top in local_modules or module_path in local_modules


def _parse_import_statement(
    node, source: bytes, local_modules: frozenset[str]
) -> list[dict[str, Any]]:
    src_node = node.child_by_field_name("source")
    if src_node is None or src_node.type != "string":
        return []
    module = _strip_string_quotes(_node_text(src_node, source))
    is_local = _is_local_module(module, local_modules)

    import_clause = None
    for child in node.children:
        if child.type == "import_clause":
            import_clause = child
            break
    if import_clause is None:
        # Side-effect import: no symbols. Skip — matches Python's behaviour
        # where bare ``import x`` for side-effects still appears in the AST,
        # but here we have nothing to bind.
        return []

    default_alias: str | None = None
    namespace_alias: str | None = None
    named: list[tuple[str, str]] = []  # (name, alias)

    for c in import_clause.children:
        if c.type == "identifier":
            default_alias = _node_text(c, source)
        elif c.type == "namespace_import":
            for spec in c.children:
                if spec.type == "identifier":
                    namespace_alias = _node_text(spec, source)
        elif c.type == "named_imports":
            for spec in c.children:
                if spec.type == "import_specifier":
                    name_node = spec.child_by_field_name("name")
                    alias_node = spec.child_by_field_name("alias")
                    if name_node is None:
                        continue
                    nm = _node_text(name_node, source)
                    al = _node_text(alias_node, source) if alias_node else nm
                    named.append((nm, al))

    out: list[dict[str, Any]] = []
    if default_alias is not None:
        out.append(
            {
                "kind": "from",
                "module": module,
                "names": ["default"],
                "asnames": [default_alias],
                "is_local": is_local,
                "level": 0,
            }
        )
    if namespace_alias is not None:
        out.append(
            {
                "kind": "import",
                "module": module,
                "names": [module],
                "asnames": [namespace_alias],
                "is_local": is_local,
                "level": 0,
            }
        )
    if named:
        out.append(
            {
                "kind": "from",
                "module": module,
                "names": [n for n, _ in named],
                "asnames": [a for _, a in named],
                "is_local": is_local,
                "level": 0,
            }
        )
    return out


def _parse_require_call(
    node, source: bytes, local_modules: frozenset[str]
) -> dict[str, Any] | None:
    func = node.child_by_field_name("function")
    if func is None or func.type != "identifier":
        return None
    if _node_text(func, source) != "require":
        return None
    args = node.child_by_field_name("arguments")
    if args is None:
        return None
    string_arg = None
    for c in args.children:
        if c.type == "string":
            string_arg = c
            break
    if string_arg is None:
        return None
    module = _strip_string_quotes(_node_text(string_arg, source))
    is_local = _is_local_module(module, local_modules)

    parent = node.parent
    while parent is not None and parent.type != "variable_declarator":
        parent = parent.parent
    if parent is None:
        # Bare ``require("x")`` for side-effects — no binding to record.
        return None

    name_node = parent.child_by_field_name("name")
    if name_node is None:
        return None

    if name_node.type == "identifier":
        n = _node_text(name_node, source)
        return {
            "kind": "import",
            "module": module,
            "names": [module],
            "asnames": [n],
            "is_local": is_local,
            "level": 0,
        }
    if name_node.type == "object_pattern":
        names: list[str] = []
        asnames: list[str] = []
        for c in name_node.children:
            if c.type == "shorthand_property_identifier_pattern":
                nm = _node_text(c, source)
                names.append(nm)
                asnames.append(nm)
            elif c.type == "object_assignment_pattern":
                for cc in c.children:
                    if cc.type == "shorthand_property_identifier_pattern":
                        nm = _node_text(cc, source)
                        names.append(nm)
                        asnames.append(nm)
                        break
            elif c.type == "pair_pattern":
                key_node = c.child_by_field_name("key")
                value_node = c.child_by_field_name("value")
                if key_node is not None and value_node is not None:
                    names.append(_node_text(key_node, source))
                    asnames.append(_node_text(value_node, source))
        if not names:
            return None
        return {
            "kind": "from",
            "module": module,
            "names": names,
            "asnames": asnames,
            "is_local": is_local,
            "level": 0,
        }
    return None
