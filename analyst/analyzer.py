import ast
import builtins as _py_builtins
import functools
import hashlib
import os
import sys
import time
import threading
from collections import OrderedDict
import networkx as nx
from typing import Any


IGNORED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "site-packages",
        "venv",
        "env",
        ".venv",
        "__pycache__",
    }
)

MAX_FILE_SIZE = 1024 * 1024  # 1MB per-file limit to prevent Asymmetric DoS

_ROUTE_DECORATOR_NAMES = frozenset({"get", "post", "put", "patch", "delete", "route"})
_ROUTE_DECORATOR_SUFFIXES = (".get", ".post", ".put", ".patch", ".delete", ".route")
# HTTP verb names (get/post/put/patch/delete) are intentionally excluded — they
# collide with `dict.get`, `cache.get`, `os.environ.get`, etc. API boundary
# detection via decorators already covers FastAPI/Flask routes.
_SIDE_EFFECT_CALLS = frozenset(
    {
        "open",
        "read",
        "write",
        "remove",
        "unlink",
        "rmtree",
        "copy",
        "move",
        "request",
        "run",
        "popen",
        "connect",
        "execute",
    }
)
_SIDE_EFFECT_MODULES = frozenset(
    {"os", "shutil", "subprocess", "requests", "httpx", "boto3", "socket"}
)
_NESTING_NODE_TYPES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Match,
)

# Python's built-in callables (print, len, range, open, str, ...). Used to tag
# call targets that hit the language runtime so the frontend can render them
# distinctly from user code or imports instead of falling back to the gray
# "unresolved reference" style.
PY_BUILTINS = frozenset(name for name in dir(_py_builtins) if not name.startswith("_"))

# Heuristic list of common stdlib top-level modules. When a call's base
# (e.g. `os` in `os.path.exists`) matches one of these and there's no matching
# import in the file, we still tag it as external rather than unresolved. The
# set is intentionally narrow — only well-known modules — to avoid mis-tagging
# user variables.
STDLIB_MODULES = frozenset(
    {
        "os",
        "sys",
        "json",
        "re",
        "math",
        "time",
        "random",
        "collections",
        "itertools",
        "functools",
        "typing",
        "pathlib",
        "datetime",
        "logging",
        "asyncio",
        "threading",
        "subprocess",
        "shutil",
        "tempfile",
        "io",
        "string",
        "csv",
        "argparse",
        "abc",
        "copy",
        "enum",
        "hashlib",
        "uuid",
        "base64",
        "warnings",
        "contextlib",
        "dataclasses",
        "inspect",
        "ast",
        "traceback",
        "weakref",
        "operator",
        "socket",
        "urllib",
        "http",
    }
)

# Content-hash AST cache. Skips repeat ast.parse() on identical bytes across
# uploads, identical files (e.g. empty __init__.py), and CI re-runs. Cache the
# ast.Module — NOT the per-file DiGraph — because CallGraphVisitor stamps
# file_path into every node's `file=` attribute (consumed by the snippet
# preview), so two paths with identical bytes must still produce path-tagged
# graphs. The visitor walk is cheap; only the parse is expensive.
#
# Do not mutate cached ast.Module objects (no .parent backrefs, no
# fix_missing_locations) — they are shared by reference.
_AST_CACHE_MAX = 256
_AST_CACHE: "OrderedDict[bytes, ast.Module]" = OrderedDict()
_AST_CACHE_LOCK = threading.Lock()
# Thread-local accumulator for ?profile=1 parse timing. Set to a dict before
# a parse pass; _parse_cached writes into it; cleared after the pass.
_PROFILE_DATA = threading.local()
# Python version in the key invalidates across upgrades (e.g. 3.11 -> 3.12
# adds ast.TryStar). FastAPI runs sync handlers in a threadpool, so the lock
# is mandatory: OrderedDict mutations are not thread-safe.
_AST_CACHE_VERSION_TAG = repr(sys.version_info[:2]).encode()


def _parse_cached(source: bytes, filename: str) -> ast.Module:
    prof = getattr(_PROFILE_DATA, "data", None)
    t0 = time.perf_counter() if prof is not None else 0.0
    key = hashlib.sha256(source).digest() + _AST_CACHE_VERSION_TAG
    with _AST_CACHE_LOCK:
        hit = _AST_CACHE.get(key)
        if hit is not None:
            _AST_CACHE.move_to_end(key)
            if prof is not None:
                prof["parse_count"] = prof.get("parse_count", 0) + 1
                prof["parse_cached_hits"] = prof.get("parse_cached_hits", 0) + 1
                prof["parse_total_ms"] = (
                    prof.get("parse_total_ms", 0.0) + (time.perf_counter() - t0) * 1000
                )
            return hit
    tree = ast.parse(source, filename=filename)
    with _AST_CACHE_LOCK:
        _AST_CACHE[key] = tree
        _AST_CACHE.move_to_end(key)
        if len(_AST_CACHE) > _AST_CACHE_MAX:
            _AST_CACHE.popitem(last=False)
    if prof is not None:
        prof["parse_count"] = prof.get("parse_count", 0) + 1
        prof["parse_total_ms"] = (
            prof.get("parse_total_ms", 0.0) + (time.perf_counter() - t0) * 1000
        )
    return tree


def _ast_cache_clear() -> None:
    with _AST_CACHE_LOCK:
        _AST_CACHE.clear()


def _file_to_module_id(file_path: str, project_root: str | None) -> str:
    """Convert a .py path to a dotted module id (e.g. pkg/a.py -> pkg.a).

    Returns just the basename (without .py) when project_root is unknown or the
    file lives outside it. The returned id is wrapped in the "module:" prefix
    by callers to keep module nodes from colliding with function/class nodes.
    """
    if project_root:
        try:
            rel = os.path.relpath(file_path, project_root)
        except ValueError:
            rel = os.path.basename(file_path)
    else:
        rel = os.path.basename(file_path)
    rel = rel.replace(os.sep, "/")
    if rel.endswith(".py"):
        rel = rel[:-3]
    if rel.endswith("/__init__"):
        rel = rel[: -len("/__init__")]
    return rel.replace("/", ".") or os.path.basename(file_path)


def _extract_imports(tree: ast.Module, local_modules: frozenset[str]) -> list[dict]:
    """Walk an AST module and return its import statements as a flat list.

    Each entry: {kind, module, names, asnames, is_local, level}. ``names`` is
    the list of imported symbols (raw names) and ``asnames`` is the parallel
    list of local aliases (asname or original name). For ``import X``, both
    contain ``X``; for ``from M import Y as Z``, ``names=["Y"]`` and
    ``asnames=["Z"]``.
    """
    out: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                top = module.split(".")[0]
                out.append(
                    {
                        "kind": "import",
                        "module": module,
                        "names": [module],
                        "asnames": [alias.asname or module],
                        "is_local": module in local_modules or top in local_modules,
                        "level": 0,
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            top = module.split(".")[0] if module else ""
            is_local = node.level > 0 or module in local_modules or top in local_modules
            out.append(
                {
                    "kind": "from",
                    "module": module,
                    "names": [a.name for a in node.names],
                    "asnames": [a.asname or a.name for a in node.names],
                    "is_local": is_local,
                    "level": node.level,
                }
            )
    return out


class CallGraphVisitor(ast.NodeVisitor):
    """AST visitor that records function/class definitions and queues calls.

    Calls are NOT immediately added as edges — they are stored in
    ``pending_calls`` so that a second pass with full cross-file knowledge
    (symbol table, imports) can resolve them to typed targets. This is what
    eliminates the gray "unknown reference" nodes for built-ins, imports and
    self-method calls.
    """

    def __init__(self, file_path: str):
        self.graph = nx.DiGraph()
        self.current_scope = "global"
        self.class_stack: list[str] = []
        self.definitions: list[dict[str, Any]] = []
        self.top_level_definitions: list[dict[str, Any]] = []
        self.file_path = file_path
        self.pending_calls: list[tuple[str, dict]] = []

    def _metadata_for_definition(self, node, name: str) -> dict[str, Any]:
        end_lineno = getattr(node, "end_lineno", node.lineno)

        calls: set[str] = set()
        imports_side_effect_module = False
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                callee = self._raw_callee_name(child)
                if callee:
                    calls.add(callee)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                if any(
                    (alias.name.split(".")[0] if alias.name else "")
                    in _SIDE_EFFECT_MODULES
                    for alias in child.names
                ):
                    imports_side_effect_module = True

        api_boundary = any(
            (decorator_name := self._decorator_name(decorator))
            in _ROUTE_DECORATOR_NAMES
            or decorator_name.endswith(_ROUTE_DECORATOR_SUFFIXES)
            for decorator in getattr(node, "decorator_list", [])
        )

        side_effect_boundary = (
            api_boundary
            or imports_side_effect_module
            or bool(calls & _SIDE_EFFECT_CALLS)
        )

        return {
            "end_lineno": end_lineno,
            "loc": max(end_lineno - node.lineno + 1, 1),
            "nesting_depth": self._max_nesting_depth(node),
            "dependency_count": len(calls),
            "public_api": not name.rsplit(".", 1)[-1].startswith("_"),
            "api_boundary": api_boundary,
            "side_effect_boundary": side_effect_boundary,
        }

    def _decorator_name(self, node) -> str:
        if isinstance(node, ast.Call):
            return self._decorator_name(node.func)
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._decorator_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    def _max_nesting_depth(self, node) -> int:
        def walk(child, depth: int) -> int:
            next_depth = depth + 1 if isinstance(child, _NESTING_NODE_TYPES) else depth
            return max(
                (walk(g, next_depth) for g in ast.iter_child_nodes(child)),
                default=next_depth,
            )

        return max(
            (walk(child, 0) for child in ast.iter_child_nodes(node)),
            default=0,
        )

    def visit_FunctionDef(self, node):
        previous_scope = self.current_scope
        function_name = node.name
        # If in a class, prefix with class name (simplified)
        if self.current_scope != "global" and not self.current_scope.endswith(
            "<module>"
        ):
            full_name = f"{self.current_scope}.{function_name}"
        else:
            full_name = function_name

        self.current_scope = full_name
        is_top_level = previous_scope in ("global", "<module>")

        # Entry-point heuristics:
        #   1. Well-known names: main, run, app
        #   2. Any function at module (global) level
        is_entry = function_name in ["main", "run", "app"] or is_top_level
        self.graph.add_node(
            full_name,
            type="function",
            lineno=node.lineno,
            docstring=ast.get_docstring(node),
            file=self.file_path,
            entry_point=is_entry,
            **self._metadata_for_definition(node, full_name),
        )
        record = {"name": full_name, "type": "function", "lineno": node.lineno}
        self.definitions.append(record)
        if is_top_level:
            self.top_level_definitions.append(record)

        self.generic_visit(node)
        self.current_scope = previous_scope

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        previous_scope = self.current_scope
        class_name = node.name
        is_top_level = previous_scope in ("global", "<module>")
        self.current_scope = class_name
        self.class_stack.append(class_name)

        self.graph.add_node(
            class_name,
            type="class",
            lineno=node.lineno,
            docstring=ast.get_docstring(node),
            file=self.file_path,
            entry_point=False,
            **self._metadata_for_definition(node, class_name),
        )
        record = {"name": class_name, "type": "class", "lineno": node.lineno}
        self.definitions.append(record)
        if is_top_level:
            self.top_level_definitions.append(record)

        self.generic_visit(node)
        self.class_stack.pop()
        self.current_scope = previous_scope

    def visit_Call(self, node):
        info = self._extract_callee(node)
        if info is not None:
            info["lineno"] = getattr(node, "lineno", None)
            self.pending_calls.append((self.current_scope, info))
        self.generic_visit(node)

    def _raw_callee_name(self, node) -> str | None:
        """Cheap callee name used by side-effect heuristics (unchanged contract)."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _extract_callee(self, node) -> dict | None:
        """Classify a Call AST into an info dict for later resolution.

        Kinds:
          - ``name``: bare ``foo()`` -> ``{"kind":"name", "name":"foo"}``
          - ``self_method``: ``self.foo()`` / ``cls.foo()`` inside a class
          - ``attribute``: ``obj.foo()`` / ``a.b.foo()`` -> includes base+chain
        """
        func = node.func
        if isinstance(func, ast.Name):
            return {"kind": "name", "name": func.id}

        if isinstance(func, ast.Attribute):
            # Walk the attribute chain right-to-left to recover the full path.
            parts: list[str] = []
            cur: ast.AST = func
            while isinstance(cur, ast.Attribute):
                parts.insert(0, cur.attr)
                cur = cur.value
            attr_name = parts[-1] if parts else ""
            if isinstance(cur, ast.Name):
                base = cur.id
                if base in ("self", "cls") and len(parts) == 1 and self.class_stack:
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
            # Chained call like func()(x) or subscript[x](): we still record
            # the rightmost attr name so it appears in the graph somewhere.
            if attr_name:
                return {
                    "kind": "attribute",
                    "name": attr_name,
                    "base": None,
                    "parts": parts,
                }
        return None


class CodeAnalyzer:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.definitions = []
        self.errors = []

    def analyze_file(self, target_path: str, _profile: dict | None = None) -> dict[str, Any]:
        """
        Analyzes a file or directory recursively.
        """
        # Reset graph and errors for fresh analysis
        self.graph = nx.DiGraph()
        self.definitions = []
        self.errors = []

        if not os.path.exists(target_path):
            safe_path = os.path.basename(target_path)
            return {"error": f"Path not found: {safe_path}"}

        if os.path.isdir(target_path):
            return self._analyze_directory(target_path, _profile=_profile)
        else:
            if os.path.getsize(target_path) > MAX_FILE_SIZE:
                safe_path = os.path.basename(target_path)
                return {
                    "error": f"File exceeds maximum allowed size ({MAX_FILE_SIZE} bytes): {safe_path}"
                }
            return self._analyze_single_file(target_path)

    # ------------------------------------------------------------------
    # Directory analysis (two-pass: collect definitions, then resolve calls)
    # ------------------------------------------------------------------

    def _analyze_directory(self, dir_path: str, _profile: dict | None = None) -> dict[str, Any]:
        # Lazy import to avoid the analyst.languages → analyst.analyzer import
        # cycle (the Python plugin imports CallGraphVisitor from this module).
        from analyst.languages import get_analyzer_for_path

        self.graph = nx.DiGraph()
        self.definitions = []

        # ---- Walk filesystem; pick a language plugin for each file ----
        files: list[tuple[str, str, Any]] = []  # (file_path, safe_name, analyzer)
        _t_walk = time.perf_counter() if _profile is not None else 0.0
        stack = [dir_path]
        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for dir_entry in it:
                        if dir_entry.is_dir(follow_symlinks=False):
                            if dir_entry.name not in IGNORED_DIRS:
                                stack.append(dir_entry.path)
                        elif dir_entry.is_file():
                            language_analyzer = get_analyzer_for_path(dir_entry.path)
                            if language_analyzer is None:
                                continue
                            try:
                                rel = os.path.relpath(dir_entry.path, dir_path)
                            except ValueError:
                                rel = dir_entry.name
                            safe = rel.replace(os.sep, "/")
                            try:
                                size = dir_entry.stat().st_size
                            except OSError:
                                size = 0
                            if size > MAX_FILE_SIZE:
                                self.errors.append(
                                    f"File exceeds maximum allowed size ({MAX_FILE_SIZE} bytes): {safe}"
                                )
                                continue
                            files.append((dir_entry.path, safe, language_analyzer))
            except OSError:
                self.errors.append("Error reading directory structure.")
        if _profile is not None:
            _profile["walk_ms"] = round((time.perf_counter() - _t_walk) * 1000, 2)

        # Cache local-module sets per-language for the directory so the
        # resolver doesn't rescan disk for every file.
        local_modules_by_lang: dict[str, frozenset[str]] = {}

        def _local_modules_for(lang) -> frozenset[str]:
            cached = local_modules_by_lang.get(lang.language_id)
            if cached is None:
                cached = lang.get_local_modules(dir_path)
                local_modules_by_lang[lang.language_id] = cached
            return cached

        # ---- Pass 1: parse + visit each file via its language plugin ----
        per_file: list[dict] = []
        symbol_table: dict[str, str] = {}  # short_name -> canonical id

        from analyst.languages.base import ParseError

        if _profile is not None:
            _PROFILE_DATA.data = {"parse_count": 0, "parse_cached_hits": 0, "parse_total_ms": 0.0}
        try:
            for file_path, safe_name, language_analyzer in files:
                try:
                    analysis = language_analyzer.analyze_file(file_path, dir_path)
                except ParseError as parse_err:
                    self.errors.append(parse_err.message)
                    continue
                except Exception:
                    self.errors.append(f"Could not parse {safe_name}")
                    continue
                if analysis is None:
                    self.errors.append(f"Could not parse {safe_name}")
                    continue
                per_file.append(
                    {
                        "file_path": file_path,
                        "safe_name": safe_name,
                        "analysis": analysis,
                        "analyzer": language_analyzer,
                    }
                )
                for d in analysis.top_level_definitions:
                    # First definition wins on collision (deterministic by walk order).
                    symbol_table.setdefault(d["name"], d["name"])
                self.definitions.extend(analysis.definitions)
        finally:
            if _profile is not None:
                _pd = _PROFILE_DATA.data or {}
                _profile["parse_count"] = _pd.get("parse_count", 0)
                _profile["parse_cached_hits"] = _pd.get("parse_cached_hits", 0)
                _profile["parse_total_ms"] = round(_pd.get("parse_total_ms", 0.0), 2)
                _PROFILE_DATA.data = None

        # ---- Pass 2: resolve calls into typed edges ----
        graphs: list[nx.DiGraph] = []
        stub_metadata: dict[str, dict] = {}

        for entry in per_file:
            analysis = entry["analysis"]
            language_analyzer = entry["analyzer"]
            imports = analysis.imports
            local_def_ids = set(analysis.graph.nodes())
            local_modules = _local_modules_for(language_analyzer)
            for scope, info in analysis.pending_calls:
                target_id, attrs = self._resolve_call(
                    info=info,
                    file_path=entry["file_path"],
                    imports=imports,
                    symbol_table=symbol_table,
                    local_modules=local_modules,
                    local_def_ids=local_def_ids,
                    builtins=language_analyzer.builtins,
                    stdlib_modules=language_analyzer.stdlib_modules,
                )
                analysis.graph.add_edge(scope, target_id)
                if attrs is not None:
                    existing = stub_metadata.get(target_id)
                    if existing is None or _is_better_stub(attrs, existing):
                        stub_metadata[target_id] = attrs
            graphs.append(analysis.graph)

        _t_compose = time.perf_counter() if _profile is not None else 0.0
        if graphs:
            self.graph = nx.compose_all(graphs)
        if _profile is not None:
            _profile["compose_all_ms"] = round((time.perf_counter() - _t_compose) * 1000, 2)

        # ---- Add module nodes + contains/imports edges ----
        self._add_module_nodes(per_file, dir_path, symbol_table)

        # ---- Enrich any stub-only nodes with metadata ----
        for node_id, attrs in stub_metadata.items():
            if node_id in self.graph:
                existing = self.graph.nodes[node_id]
                if not existing.get("type"):
                    existing.update(attrs)
            else:
                # add_edge would have created it, but just in case:
                self.graph.add_node(node_id, **attrs)

        # ---- Final safety net: any remaining type-less node becomes "unresolved" ----
        for node_id, data in self.graph.nodes(data=True):
            if not data.get("type"):
                data["type"] = "unresolved"
                data.setdefault("label", node_id)

        return {
            "file": dir_path,
            "definitions": self.definitions,
            "graph": self.graph,
            "errors": self.errors,
        }

    # ------------------------------------------------------------------
    # Single-file analysis
    # ------------------------------------------------------------------

    def _analyze_single_file(
        self, file_path: str, merge: bool = False, root: str | None = None
    ) -> dict[str, Any]:
        from analyst.languages import get_analyzer_for_path

        if merge and root is not None:
            try:
                rel = os.path.relpath(file_path, root)
            except ValueError:
                rel = os.path.basename(file_path)
            safe_name = rel.replace(os.sep, "/")
        else:
            safe_name = os.path.basename(file_path)

        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            error_msg = f"File exceeds maximum allowed size ({MAX_FILE_SIZE} bytes): {safe_name}"
            if merge:
                self.errors.append(error_msg)
                return {}
            return {"error": error_msg}

        language_analyzer = get_analyzer_for_path(file_path)
        if language_analyzer is None:
            error_msg = f"Unsupported file type: {safe_name}"
            if merge:
                self.errors.append(error_msg)
                return {}
            return {"error": error_msg}

        from analyst.languages.base import ParseError

        project_root = os.path.dirname(os.path.abspath(file_path))
        err: str | None = None
        analysis = None
        try:
            analysis = language_analyzer.analyze_file(file_path, project_root)
        except ParseError as parse_err:
            err = parse_err.message
        except Exception:
            err = f"Could not parse {safe_name}"
        if analysis is None:
            if err is None:
                err = f"Could not parse {safe_name}"
            self.errors.append(err)
            if merge:
                return {}
            return {"error": err}

        graph = analysis.graph
        # Build a single-file symbol table from this file's definitions only.
        symbol_table = {d["name"]: d["name"] for d in analysis.top_level_definitions}
        local_modules = language_analyzer.get_local_modules(project_root)

        local_def_ids = set(graph.nodes())
        stub_metadata: dict[str, dict] = {}
        for scope, info in analysis.pending_calls:
            target_id, attrs = self._resolve_call(
                info=info,
                file_path=file_path,
                imports=analysis.imports,
                symbol_table=symbol_table,
                local_modules=local_modules,
                local_def_ids=local_def_ids,
                builtins=language_analyzer.builtins,
                stdlib_modules=language_analyzer.stdlib_modules,
            )
            graph.add_edge(scope, target_id)
            if attrs is not None:
                existing = stub_metadata.get(target_id)
                if existing is None or _is_better_stub(attrs, existing):
                    stub_metadata[target_id] = attrs

        # Apply stub metadata to nodes that have no type yet.
        for node_id, attrs in stub_metadata.items():
            if node_id in graph:
                existing = graph.nodes[node_id]
                if not existing.get("type"):
                    existing.update(attrs)
            else:
                graph.add_node(node_id, **attrs)

        # Add a module node and contains edges for this single file.
        module_id = "module:" + language_analyzer.module_id_from_path(
            file_path, project_root
        )
        if module_id not in graph:
            graph.add_node(
                module_id,
                type="module",
                file=file_path,
                label=os.path.basename(file_path),
                entry_point=False,
                language=language_analyzer.language_id,
            )
        for d in analysis.top_level_definitions:
            if d["name"] in graph:
                graph.add_edge(module_id, d["name"], edge_type="contains")

        # Final safety: any remaining type-less node becomes "unresolved".
        for node_id, data in graph.nodes(data=True):
            if not data.get("type"):
                data["type"] = "unresolved"
                data.setdefault("label", node_id)

        if merge:
            self.definitions.extend(analysis.definitions)
        else:
            self.graph = graph
            self.definitions = analysis.definitions

        return {
            "file": file_path,
            "definitions": analysis.definitions,
            "graph": graph,
        }

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _parse_and_visit(
        self,
        file_path: str,
        safe_name: str,
        merge: bool,
        project_root: str | None = None,
    ) -> dict | None:
        """Read, parse, walk one file. Returns None on error (and records it).

        ``project_root`` controls which directory is scanned to determine which
        imports are "local". Directory mode passes the upload root so that
        ``from pkg.sub import X`` is recognised as local even when the file
        being parsed is itself nested inside ``pkg/sub/``.
        """
        try:
            with open(file_path, "rb") as f:
                source = f.read()
            tree = _parse_cached(source, filename=file_path)
        except SyntaxError:
            err = f"Syntax error in {safe_name}"
        except (UnicodeDecodeError, ValueError):
            err = f"Could not decode {safe_name}"
        except OSError:
            err = f"Could not read {safe_name}"
        else:
            visitor = CallGraphVisitor(file_path)
            visitor.visit(tree)
            scan_root = project_root or os.path.dirname(os.path.abspath(file_path))
            local_modules = CodeAnalyzer._get_local_modules(scan_root)
            imports = _extract_imports(tree, local_modules)
            return {
                "file_path": file_path,
                "tree": tree,
                "visitor": visitor,
                "imports": imports,
            }

        self.errors.append(err)
        return None

    def _resolve_call(
        self,
        info: dict,
        file_path: str,
        imports: list[dict],
        symbol_table: dict[str, str],
        local_modules: frozenset[str],
        local_def_ids: set[str],
        builtins: frozenset[str] = PY_BUILTINS,
        stdlib_modules: frozenset[str] = STDLIB_MODULES,
    ) -> tuple[str, dict | None]:
        """Resolve a queued call to a graph node id and (optional) stub attrs.

        Returns (target_id, attrs). If ``attrs`` is None, the target is a real
        definition (already a node with full metadata) and no stub creation is
        needed. Otherwise ``attrs`` describes the typed stub to register.
        """
        kind = info["kind"]
        name = info["name"]

        # ---- self.X / cls.X inside a class body ----
        if kind == "self_method":
            qualified = f"{info['class']}.{name}"
            if qualified in local_def_ids:
                return qualified, None
            # Not a local method — likely inherited or dynamically attached.
            stub_id = f"unresolved:{qualified}"
            return stub_id, {
                "type": "unresolved",
                "label": qualified,
                "file": None,
            }

        # ---- bare-name calls: foo() ----
        if kind == "name":
            # 1. Defined in this file
            if name in local_def_ids:
                return name, None
            # 2. Built-in (per-language)
            if name in builtins:
                stub_id = f"builtin:{name}"
                return stub_id, {
                    "type": "builtin",
                    "label": name,
                    "file": None,
                }
            # 3. Brought in via `from M import name [as alias]`
            for imp in imports:
                if imp["kind"] != "from":
                    continue
                if name in imp["asnames"]:
                    # Map the local alias back to the original symbol name.
                    idx = imp["asnames"].index(name)
                    real_name = imp["names"][idx]
                    if imp["is_local"] and real_name in symbol_table:
                        # Cross-file local resolution: link to the canonical
                        # node already produced by the defining file.
                        return symbol_table[real_name], None
                    if imp["is_local"]:
                        stub_id = (
                            f"local:{imp['module']}.{real_name}"
                            if imp["module"]
                            else real_name
                        )
                        return stub_id, {
                            "type": "imported_local",
                            "label": real_name,
                            "module": imp["module"] or None,
                            "file": None,
                        }
                    label = (
                        f"{imp['module']}.{real_name}" if imp["module"] else real_name
                    )
                    stub_id = f"external:{label}"
                    return stub_id, {
                        "type": "external",
                        "label": label,
                        "module": imp["module"] or None,
                        "file": None,
                    }
            # 4. Cross-file canonical match (no explicit import; rare but useful)
            if name in symbol_table:
                return symbol_table[name], None
            # 5. Final fallthrough
            stub_id = f"unresolved:{name}"
            return stub_id, {
                "type": "unresolved",
                "label": name,
                "file": None,
            }

        # ---- attribute calls: obj.foo() / module.foo() / a.b.c.foo() ----
        if kind == "attribute":
            base = info.get("base")
            parts = info.get("parts") or [name]

            # Try to map the base to an imported module / alias.
            if base is not None:
                for imp in imports:
                    if imp["kind"] == "import":
                        # `import M [as alias]` -> alias is in asnames
                        for alias in imp["asnames"]:
                            top = alias.split(".")[0]
                            if base == top or base == alias:
                                full = f"{imp['module']}." + ".".join(parts)
                                if imp["is_local"]:
                                    if name in symbol_table:
                                        return symbol_table[name], None
                                    stub_id = f"local:{full}"
                                    return stub_id, {
                                        "type": "imported_local",
                                        "label": full,
                                        "module": imp["module"],
                                        "file": None,
                                    }
                                stub_id = f"external:{full}"
                                return stub_id, {
                                    "type": "external",
                                    "label": full,
                                    "module": imp["module"],
                                    "file": None,
                                }
                    elif imp["kind"] == "from":
                        # `from M import X` -> X.method() means base==X
                        if base in imp["asnames"]:
                            idx = imp["asnames"].index(base)
                            real_name = imp["names"][idx]
                            full_label = ".".join([real_name] + parts)
                            if imp["is_local"]:
                                # If X is a class we ingested, map to X.method
                                qualified = f"{real_name}.{name}"
                                if qualified in symbol_table:
                                    return symbol_table[qualified], None
                                stub_id = (
                                    f"local:{imp['module']}.{full_label}"
                                    if imp["module"]
                                    else f"local:{full_label}"
                                )
                                return stub_id, {
                                    "type": "imported_local",
                                    "label": full_label,
                                    "module": imp["module"] or None,
                                    "file": None,
                                }
                            ext_label = (
                                f"{imp['module']}.{full_label}"
                                if imp["module"]
                                else full_label
                            )
                            stub_id = f"external:{ext_label}"
                            return stub_id, {
                                "type": "external",
                                "label": ext_label,
                                "module": imp["module"] or None,
                                "file": None,
                            }

                # Stdlib fallback: os.path.exists(), json.loads(), etc.
                if base in stdlib_modules:
                    full = f"{base}." + ".".join(parts)
                    stub_id = f"external:{full}"
                    return stub_id, {
                        "type": "external",
                        "label": full,
                        "module": base,
                        "file": None,
                    }

            # If just the method name happens to match a known qualified
            # method (e.g. `obj.run()` and `Foo.run` exists), skip — too
            # ambiguous without type inference. Fall through to unresolved.
            stub_id = f"unresolved:{name}"
            return stub_id, {
                "type": "unresolved",
                "label": name,
                "file": None,
            }

        # Defensive default — should not happen.
        stub_id = f"unresolved:{name}"
        return stub_id, {
            "type": "unresolved",
            "label": name,
            "file": None,
        }

    def _add_module_nodes(
        self,
        per_file: list[dict],
        project_root: str,
        symbol_table: dict[str, str],
    ) -> None:
        """Add a `module:<dotted>` node per file plus contains/imports edges.

        Module nodes give the graph a coarse top-level structure: every
        function/class is anchored to the file it lives in, and cross-file
        imports show up as inter-module arrows so the user can read the
        project's high-level shape at a glance. Module ids are computed by
        each file's language plugin (Python strips ``.py`` and ``__init__``;
        JavaScript strips ``.js / .jsx / .mjs / .cjs`` and ``index``).
        """
        for entry in per_file:
            analysis = entry["analysis"]
            language_analyzer = entry["analyzer"]
            if not analysis.top_level_definitions and not analysis.pending_calls:
                entry["module_id"] = None
                continue
            mod_id = "module:" + language_analyzer.module_id_from_path(
                entry["file_path"], project_root
            )
            entry["module_id"] = mod_id
            self.graph.add_node(
                mod_id,
                type="module",
                file=entry["file_path"],
                label=os.path.basename(entry["file_path"]),
                entry_point=False,
                language=language_analyzer.language_id,
            )

        # contains: module -> top-level definitions in that file.
        for entry in per_file:
            mod_id = entry["module_id"]
            if mod_id is None:
                continue
            for d in entry["analysis"].top_level_definitions:
                if d["name"] in self.graph:
                    self.graph.add_edge(mod_id, d["name"], edge_type="contains")

        # imports: module -> module (only for local imports we can resolve).
        module_id_by_dotted: dict[str, str] = {}
        for entry in per_file:
            if entry["module_id"] is None:
                continue
            dotted = entry["analyzer"].module_id_from_path(
                entry["file_path"], project_root
            )
            module_id_by_dotted[dotted] = entry["module_id"]

        for entry in per_file:
            mod_id = entry["module_id"]
            if mod_id is None:
                continue
            seen: set[str] = set()
            for imp in entry["analysis"].imports:
                if not imp["is_local"]:
                    continue
                target_dotted = imp["module"]
                if not target_dotted:
                    continue
                # Try direct match, then progressively shorter prefixes for
                # `from pkg.sub import X` style imports. JS imports use
                # relative paths like ``./foo`` — those don't match anything
                # in module_id_by_dotted (which keys by dotted name), so they
                # fall through to "no edge" silently. That's acceptable for
                # the first pass; cross-file JS edges are nice-to-have.
                target_node = module_id_by_dotted.get(target_dotted)
                if target_node is None:
                    parts = target_dotted.split(".")
                    while parts and target_node is None:
                        parts.pop()
                        target_node = module_id_by_dotted.get(".".join(parts))
                if target_node is None or target_node == mod_id:
                    continue
                if target_node in seen:
                    continue
                seen.add(target_node)
                self.graph.add_edge(mod_id, target_node, edge_type="imports")

    # ------------------------------------------------------------------
    # Dependency extraction via import analysis
    # ------------------------------------------------------------------

    def extract_dependencies(
        self, file_path: str, project_root: str | None = None
    ) -> dict[str, Any]:
        """
        Extracts import statements from *file_path* using AST.

        Parameters
        ----------
        file_path : str
            Path to the Python source file.
        project_root : str, optional
            Root of the project. Used to detect local (project-internal)
            imports by checking whether a corresponding ``.py`` file exists.
            Defaults to the directory containing *file_path*.

        Returns
        -------
        dict with keys ``file`` and ``dependencies``.
        Each dependency: ``{"module": str, "names": [str], "is_local": bool}``
        """
        resolved = os.path.abspath(file_path)
        safe_name = os.path.basename(file_path)
        if not os.path.isfile(resolved):
            return {"error": f"File not found: {safe_name}"}

        if os.path.getsize(resolved) > MAX_FILE_SIZE:
            return {
                "error": f"File exceeds maximum allowed size ({MAX_FILE_SIZE} bytes): {safe_name}"
            }

        if project_root is None:
            project_root = os.path.dirname(resolved)
        project_root = os.path.abspath(project_root)

        try:
            with open(resolved, "rb") as f:
                source = f.read()
            tree = _parse_cached(source, filename=resolved)
        except SyntaxError:
            return {"error": f"Syntax error in {safe_name}"}
        except (UnicodeDecodeError, ValueError):
            return {"error": f"Could not decode {safe_name}"}
        except OSError:
            return {"error": f"Could not read {safe_name}"}

        local_modules = CodeAnalyzer._get_local_modules(project_root)
        raw = _extract_imports(tree, local_modules)
        # Backwards-compat shape: keep the old fields the existing tests and
        # API consumers depend on (module, names, is_local).
        dependencies = [
            {
                "module": imp["module"],
                "names": imp["asnames"] if imp["kind"] == "import" else imp["names"],
                "is_local": imp["is_local"],
            }
            for imp in raw
        ]
        return {"file": file_path, "dependencies": dependencies}

    @staticmethod
    @functools.lru_cache(maxsize=32)
    def _get_local_modules(project_root: str) -> frozenset[str]:
        """
        Scans project_root once and returns a frozenset of all local module/package
        paths in python dotted notation (e.g. 'app', 'app.routers', 'serve').
        """
        local_mods = set()

        # PERFORMANCE OPTIMIZATION (Bolt): Use os.scandir() instead of os.walk()
        # to avoid unnecessary object allocation and overhead.
        stack: list[tuple[str, list[str]]] = [(project_root, [])]

        while stack:
            current_dir, base_parts = stack.pop()

            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.is_dir():
                            if entry.name not in IGNORED_DIRS:
                                new_parts = base_parts + [entry.name]
                                local_mods.add(".".join(new_parts))
                                stack.append((entry.path, new_parts))
                        elif entry.is_file() and entry.name.endswith(".py"):
                            mod_name = entry.name[:-3]
                            if mod_name == "__init__":
                                continue
                            local_mods.add(".".join(base_parts + [mod_name]))
            except OSError:
                pass

        return frozenset(local_mods)


# Stub-attribute precedence: a more specific type beats a more generic one if
# two callsites resolve the same id (e.g. once as builtin, once as unresolved
# from a syntactically odd attribute chain). Keeps the most informative tag.
_STUB_TYPE_RANK = {
    "builtin": 4,
    "external": 3,
    "imported_local": 3,
    "module": 2,
    "unresolved": 1,
}


def _is_better_stub(new_attrs: dict, existing: dict) -> bool:
    new_rank = _STUB_TYPE_RANK.get(new_attrs.get("type", ""), 0)
    cur_rank = _STUB_TYPE_RANK.get(existing.get("type", ""), 0)
    return new_rank > cur_rank
