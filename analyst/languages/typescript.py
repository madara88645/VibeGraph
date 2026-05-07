"""TypeScript language plugin (tree-sitter).

Inherits the JavaScript analyser and:
  * picks ``tree-sitter-typescript`` (or its ``tsx`` variant) based on the
    file extension;
  * skips ``import type`` statements (they have no runtime effect, so
    creating import edges for them would clutter the graph);
  * tags methods/classes whose decorators match HTTP-route names
    (``@Get``, ``@Post``, ``@Controller`` …) as ``api_boundary=True`` —
    a small NestJS / Angular-style boost over the JS plugin.
"""

from __future__ import annotations

from typing import Any

from analyst.languages.base import FileAnalysis
from analyst.languages.javascript import (
    JavaScriptAnalyzer,
    _Walker,
    _extract_imports,
)
from analyst.tree_sitter_loader import get_parser

import os


_TSX_EXTENSIONS: frozenset[str] = frozenset({".tsx"})


_TS_ROUTE_DECORATORS: frozenset[str] = frozenset(
    {
        # NestJS / Angular HTTP method decorators (PascalCase)
        "Get",
        "Post",
        "Put",
        "Patch",
        "Delete",
        "Head",
        "Options",
        "All",
        "Controller",
        "Route",
        "Resolver",
        "Query",
        "Mutation",
        # Also lowercase variants (FastAPI-on-decorators-style)
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "route",
    }
)


class TypeScriptAnalyzer(JavaScriptAnalyzer):
    language_id = "typescript"
    display_label = "TypeScript"
    extensions: tuple[str, ...] = (".ts", ".tsx")
    _ts_language_name: str = "typescript"

    def analyze_file(
        self, file_path: str, project_root: str | None
    ) -> FileAnalysis | None:
        try:
            with open(file_path, "rb") as f:
                source = f.read()
        except (UnicodeDecodeError, ValueError, OSError):
            return None

        # Pick tsx grammar for .tsx files — JSX-like syntax is otherwise a
        # parse error in the plain typescript grammar.
        ext = os.path.splitext(file_path)[1].lower()
        lang_name = "tsx" if ext in _TSX_EXTENSIONS else "typescript"

        try:
            parser = get_parser(lang_name)
            tree = parser.parse(source)
        except Exception:
            return None
        if tree is None or tree.root_node is None:
            return None

        scan_root = project_root or os.path.dirname(os.path.abspath(file_path))
        local_modules = self.get_local_modules(scan_root)

        walker = _TypeScriptWalker(
            file_path=file_path,
            source=source,
            language_id=self.language_id,
        )
        walker.walk_module(tree.root_node)
        imports = _extract_imports(tree.root_node, source, local_modules)
        # Drop type-only imports — they leave no runtime trace, so import
        # edges for them are misleading.
        imports = [imp for imp in imports if not imp.get("_type_only")]

        return FileAnalysis(
            file_path=file_path,
            graph=walker.graph,
            top_level_definitions=list(walker.top_level_definitions),
            definitions=list(walker.definitions),
            pending_calls=list(walker.pending_calls),
            imports=imports,
        )


class _TypeScriptWalker(_Walker):
    """JS walker with two TypeScript-specific tweaks."""

    def _has_route_decorator(self, node) -> bool:
        # tree-sitter-typescript exposes ``decorator`` nodes as siblings of
        # the decorated declaration. They are listed BEFORE the function /
        # class node inside an ``export_statement`` or class body.
        # For ``@Get('/x') foo() {}`` the decorator's child is a
        # ``call_expression`` whose function is an identifier ``Get``.
        decorators = self._collect_decorators(node)
        for dec in decorators:
            name = self._decorator_name(dec)
            if name in _TS_ROUTE_DECORATORS:
                return True
            # Allow ``Module.Get`` style — match the suffix
            if "." in name and name.rsplit(".", 1)[-1] in _TS_ROUTE_DECORATORS:
                return True
        return False

    def _collect_decorators(self, node) -> list[Any]:
        decs: list[Any] = []
        # Method decorators: siblings inside class_body, preceding this method.
        # Class-level decorators: siblings inside export_statement / program,
        # preceding the class_declaration.
        parent = node.parent
        if parent is None:
            return decs
        seen_self = False
        for child in reversed(parent.children):
            if child is node:
                seen_self = True
                continue
            if not seen_self:
                continue
            if child.type == "decorator":
                decs.append(child)
            elif child.type in ("comment",):
                continue
            else:
                # Stop at the first non-decorator non-comment sibling.
                break
        return decs

    def _decorator_name(self, decorator_node) -> str:
        # decorator -> [@, expression]
        for child in decorator_node.children:
            if child.type == "@":
                continue
            if child.type == "call_expression":
                func = child.child_by_field_name("function")
                if func is not None:
                    return self._dotted_text(func)
            else:
                return self._dotted_text(child)
        return ""

    def _dotted_text(self, node) -> str:
        if node.type == "identifier":
            return self._text(node)
        if node.type == "member_expression":
            obj = node.child_by_field_name("object")
            prop = node.child_by_field_name("property")
            obj_name = self._dotted_text(obj) if obj is not None else ""
            prop_name = self._text(prop) if prop is not None else ""
            return f"{obj_name}.{prop_name}" if obj_name else prop_name
        return self._text(node)


# Patch _extract_imports with type-only awareness via a lightweight wrapper:
# we set ``_type_only`` on records that came from ``import type`` statements
# so the analyzer can drop them. Implemented inline rather than re-exporting
# to keep the patch surface tiny.

_original_parse_import_statement = None


def _patch_import_extraction() -> None:
    """Once at import time, monkey-patch the JS extractor so a type-only
    import gets a sentinel field that the TS analyser strips. The patch is
    idempotent and additive — JS imports are unaffected because non-TS
    sources never contain ``import type``.
    """
    global _original_parse_import_statement
    from analyst.languages import javascript as _js

    if getattr(_js, "_type_only_patched", False):
        return

    original = _js._parse_import_statement

    def _patched(node, source, local_modules):
        records = original(node, source, local_modules)
        if not records:
            return records
        # Detect leading ``type`` keyword in the import statement.
        is_type_only = False
        for child in node.children:
            txt = source[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            )
            if child.type == "import":
                continue
            if txt.strip() == "type":
                is_type_only = True
                break
            if child.type in ("import_clause",):
                break
        if not is_type_only:
            return records
        for r in records:
            r["_type_only"] = True
        return records

    _js._parse_import_statement = _patched
    _js._type_only_patched = True


_patch_import_extraction()
