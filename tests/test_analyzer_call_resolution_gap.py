"""Direct unit tests for pure call-classification/resolution helpers in
analyst/analyzer.py that were previously only exercised indirectly through
full-file CodeAnalyzer.analyze_file integration tests:

- CallGraphVisitor._raw_callee_name / ._extract_callee: classify an
  ast.Call node's callee into a name/self_method/attribute info dict.
- CodeAnalyzer._resolve_call: resolve a queued call's info dict to a graph
  node id (and optional stub attrs) given the file's imports and the
  cross-file symbol table. This is the highest-complexity pure resolution
  path in the analyzer (multi-branch: local def, builtin, from-import,
  plain import, stdlib fallback, cross-file symbol table, unresolved).
"""
import ast

from analyst.analyzer import CallGraphVisitor, CodeAnalyzer


def _parse_call(source: str) -> ast.Call:
    module = ast.parse(source)
    expr = module.body[0]
    assert isinstance(expr, ast.Expr)
    assert isinstance(expr.value, ast.Call)
    return expr.value


# --- _raw_callee_name ----------------------------------------------------


def test_raw_callee_name_bare_name():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("foo()")
    assert visitor._raw_callee_name(node) == "foo"


def test_raw_callee_name_attribute():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("obj.foo()")
    assert visitor._raw_callee_name(node) == "foo"


def test_raw_callee_name_deep_attribute_returns_rightmost():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("a.b.c.foo()")
    assert visitor._raw_callee_name(node) == "foo"


def test_raw_callee_name_unsupported_shape_returns_none():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("(lambda: foo)()")
    assert visitor._raw_callee_name(node) is None


# --- _extract_callee -------------------------------------------------------


def test_extract_callee_bare_name():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("foo()")
    assert visitor._extract_callee(node) == {"kind": "name", "name": "foo"}


def test_extract_callee_self_method_inside_class():
    visitor = CallGraphVisitor("test.py")
    visitor.class_stack.append("MyClass")
    node = _parse_call("self.foo()")
    assert visitor._extract_callee(node) == {
        "kind": "self_method",
        "name": "foo",
        "class": "MyClass",
    }


def test_extract_callee_cls_method_inside_class():
    visitor = CallGraphVisitor("test.py")
    visitor.class_stack.append("MyClass")
    node = _parse_call("cls.foo()")
    assert visitor._extract_callee(node) == {
        "kind": "self_method",
        "name": "foo",
        "class": "MyClass",
    }


def test_extract_callee_self_outside_class_is_attribute_not_self_method():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("self.foo()")
    assert visitor._extract_callee(node) == {
        "kind": "attribute",
        "name": "foo",
        "base": "self",
        "parts": ["foo"],
    }


def test_extract_callee_simple_attribute():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("obj.foo()")
    assert visitor._extract_callee(node) == {
        "kind": "attribute",
        "name": "foo",
        "base": "obj",
        "parts": ["foo"],
    }


def test_extract_callee_deep_attribute_chain():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("a.b.c.foo()")
    assert visitor._extract_callee(node) == {
        "kind": "attribute",
        "name": "foo",
        "base": "a",
        "parts": ["b", "c", "foo"],
    }


def test_extract_callee_chained_call_result_has_no_base():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("get_obj().foo()")
    result = visitor._extract_callee(node)
    assert result == {
        "kind": "attribute",
        "name": "foo",
        "base": None,
        "parts": ["foo"],
    }


def test_extract_callee_unsupported_shape_returns_none():
    visitor = CallGraphVisitor("test.py")
    node = _parse_call("(lambda: foo)()")
    assert visitor._extract_callee(node) is None


# --- CodeAnalyzer._resolve_call ---------------------------------------------


BUILTINS = frozenset({"print", "len"})
STDLIB = frozenset({"os", "json"})


def _resolve(info, imports=(), symbol_table=None, local_def_ids=None):
    analyzer = CodeAnalyzer()
    return analyzer._resolve_call(
        info,
        file_path="test.py",
        imports=list(imports),
        symbol_table=symbol_table or {},
        local_modules=frozenset(),
        local_def_ids=local_def_ids or set(),
        builtins=BUILTINS,
        stdlib_modules=STDLIB,
    )


def test_resolve_self_method_found_locally():
    info = {"kind": "self_method", "name": "helper", "class": "Widget"}
    target_id, attrs = _resolve(info, local_def_ids={"Widget.helper"})
    assert target_id == "Widget.helper"
    assert attrs is None


def test_resolve_self_method_not_found_becomes_unresolved_stub():
    info = {"kind": "self_method", "name": "helper", "class": "Widget"}
    target_id, attrs = _resolve(info, local_def_ids=set())
    assert target_id == "unresolved:Widget.helper"
    assert attrs == {"type": "unresolved", "label": "Widget.helper", "file": None}


def test_resolve_bare_name_local_definition():
    info = {"kind": "name", "name": "do_thing"}
    target_id, attrs = _resolve(info, local_def_ids={"do_thing"})
    assert target_id == "do_thing"
    assert attrs is None


def test_resolve_bare_name_builtin():
    info = {"kind": "name", "name": "print"}
    target_id, attrs = _resolve(info)
    assert target_id == "builtin:print"
    assert attrs == {"type": "builtin", "label": "print", "file": None}


def test_resolve_bare_name_from_import_local_with_symbol_table_hit():
    info = {"kind": "name", "name": "helper"}
    imports = [
        {
            "kind": "from",
            "module": "mypkg.util",
            "names": ["helper_impl"],
            "asnames": ["helper"],
            "is_local": True,
        }
    ]
    target_id, attrs = _resolve(
        info, imports=imports, symbol_table={"helper_impl": "mypkg.util.helper_impl"}
    )
    assert target_id == "mypkg.util.helper_impl"
    assert attrs is None


def test_resolve_bare_name_from_import_local_without_symbol_table_hit():
    info = {"kind": "name", "name": "helper"}
    imports = [
        {
            "kind": "from",
            "module": "mypkg.util",
            "names": ["helper_impl"],
            "asnames": ["helper"],
            "is_local": True,
        }
    ]
    target_id, attrs = _resolve(info, imports=imports, symbol_table={})
    assert target_id == "local:mypkg.util.helper_impl"
    assert attrs == {
        "type": "imported_local",
        "label": "helper_impl",
        "module": "mypkg.util",
        "file": None,
    }


def test_resolve_bare_name_from_import_external():
    info = {"kind": "name", "name": "loads"}
    imports = [
        {
            "kind": "from",
            "module": "json",
            "names": ["loads"],
            "asnames": ["loads"],
            "is_local": False,
        }
    ]
    target_id, attrs = _resolve(info, imports=imports)
    assert target_id == "external:json.loads"
    assert attrs == {
        "type": "external",
        "label": "json.loads",
        "module": "json",
        "file": None,
    }


def test_resolve_bare_name_cross_file_symbol_table_fallback():
    info = {"kind": "name", "name": "shared_helper"}
    target_id, attrs = _resolve(
        info, symbol_table={"shared_helper": "otherfile.shared_helper"}
    )
    assert target_id == "otherfile.shared_helper"
    assert attrs is None


def test_resolve_bare_name_final_fallthrough_unresolved():
    info = {"kind": "name", "name": "totally_unknown"}
    target_id, attrs = _resolve(info)
    assert target_id == "unresolved:totally_unknown"
    assert attrs == {"type": "unresolved", "label": "totally_unknown", "file": None}


def test_resolve_attribute_call_stdlib_fallback():
    info = {"kind": "attribute", "name": "exists", "base": "os", "parts": ["exists"]}
    target_id, attrs = _resolve(info)
    assert target_id == "external:os.exists"
    assert attrs == {
        "type": "external",
        "label": "os.exists",
        "module": "os",
        "file": None,
    }


def test_resolve_attribute_call_via_import_alias_external():
    info = {"kind": "attribute", "name": "dumps", "base": "j", "parts": ["dumps"]}
    imports = [
        {
            "kind": "import",
            "module": "json",
            "names": ["json"],
            "asnames": ["j"],
            "is_local": False,
        }
    ]
    target_id, attrs = _resolve(info, imports=imports)
    assert target_id == "external:json.dumps"
    assert attrs == {
        "type": "external",
        "label": "json.dumps",
        "module": "json",
        "file": None,
    }


def test_resolve_attribute_call_via_import_alias_local():
    info = {"kind": "attribute", "name": "run", "base": "pipeline", "parts": ["run"]}
    imports = [
        {
            "kind": "import",
            "module": "mypkg.pipeline",
            "names": ["mypkg.pipeline"],
            "asnames": ["pipeline"],
            "is_local": True,
        }
    ]
    target_id, attrs = _resolve(info, imports=imports, symbol_table={})
    assert target_id == "local:mypkg.pipeline.run"
    assert attrs == {
        "type": "imported_local",
        "label": "mypkg.pipeline.run",
        "module": "mypkg.pipeline",
        "file": None,
    }


def test_resolve_attribute_call_no_base_falls_through_to_unresolved():
    # base=None (chained call result, e.g. get_obj().foo()) can't be mapped
    # to any import, so it must fall through to the unresolved stub.
    info = {"kind": "attribute", "name": "foo", "base": None, "parts": ["foo"]}
    target_id, attrs = _resolve(info)
    assert target_id == "unresolved:foo"
    assert attrs == {"type": "unresolved", "label": "foo", "file": None}
