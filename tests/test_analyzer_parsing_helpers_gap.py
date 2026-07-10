"""Direct unit coverage for analyst.analyzer private helpers that previously
had no dedicated test — only exercised indirectly through full-file
CodeAnalyzer.analyze_file integration tests in test_analyzer.py.

_file_to_module_id and _extract_imports feed the call graph's module-node
identity and cross-file import resolution directly; _is_better_stub decides
which of two competing node-type tags wins when merging graph nodes. A bug
in any of these silently mis-wires the graph without raising an error.
"""

import ast
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst.analyzer import _extract_imports, _file_to_module_id, _is_better_stub


class TestFileToModuleId(unittest.TestCase):
    def test_nested_package_path(self):
        self.assertEqual(
            _file_to_module_id("/proj/pkg/sub/a.py", "/proj"), "pkg.sub.a"
        )

    def test_init_py_is_stripped_to_package_name(self):
        self.assertEqual(_file_to_module_id("/proj/pkg/__init__.py", "/proj"), "pkg")

    def test_no_project_root_falls_back_to_basename(self):
        self.assertEqual(_file_to_module_id("/proj/pkg/a.py", None), "a")

    def test_root_level_file(self):
        self.assertEqual(_file_to_module_id("/proj/a.py", "/proj"), "a")

    def test_file_outside_project_root_does_not_raise(self):
        # relpath() walks up with ".." rather than erroring on POSIX; the
        # function must still return a usable dotted id, not crash.
        result = _file_to_module_id("/other/x.py", "/proj")
        self.assertIsInstance(result, str)
        self.assertTrue(result)
        self.assertNotIn("/", result)

    def test_non_py_extension_is_kept_as_is(self):
        self.assertEqual(_file_to_module_id("/proj/data.json", "/proj"), "data.json")


class TestExtractImports(unittest.TestCase):
    def _imports(self, source, local_modules=frozenset()):
        tree = ast.parse(source)
        return _extract_imports(tree, local_modules)

    def test_no_imports_returns_empty_list(self):
        self.assertEqual(self._imports("x = 1\n"), [])

    def test_plain_dotted_import(self):
        result = self._imports("import a.b.c\n")
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry["kind"], "import")
        self.assertEqual(entry["module"], "a.b.c")
        self.assertEqual(entry["names"], ["a.b.c"])
        self.assertEqual(entry["asnames"], ["a.b.c"])
        self.assertEqual(entry["level"], 0)

    def test_import_with_alias(self):
        result = self._imports("import numpy as np\n")
        entry = result[0]
        self.assertEqual(entry["module"], "numpy")
        self.assertEqual(entry["names"], ["numpy"])
        self.assertEqual(entry["asnames"], ["np"])

    def test_relative_from_import_is_always_local(self):
        result = self._imports("from . import z\n")
        entry = result[0]
        self.assertEqual(entry["kind"], "from")
        self.assertEqual(entry["module"], "")
        self.assertEqual(entry["names"], ["z"])
        self.assertEqual(entry["level"], 1)
        self.assertTrue(entry["is_local"])

    def test_from_import_multiple_names_with_alias(self):
        result = self._imports("from pkg import a, b as c\n")
        entry = result[0]
        self.assertEqual(entry["module"], "pkg")
        self.assertEqual(entry["names"], ["a", "b"])
        self.assertEqual(entry["asnames"], ["a", "c"])
        self.assertEqual(entry["level"], 0)

    def test_top_level_segment_match_marks_import_as_local(self):
        result = self._imports("import pkg.sub\n", local_modules=frozenset({"pkg"}))
        self.assertTrue(result[0]["is_local"])

    def test_unmatched_module_is_not_local(self):
        result = self._imports("import requests\n", local_modules=frozenset({"pkg"}))
        self.assertFalse(result[0]["is_local"])

    def test_import_nested_inside_function_is_still_found(self):
        source = "def f():\n    import os\n"
        result = self._imports(source)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["module"], "os")

    def test_import_nested_inside_class_method_is_still_found(self):
        source = "class C:\n    def m(self):\n        from pkg import thing\n"
        result = self._imports(source, local_modules=frozenset({"pkg"}))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["module"], "pkg")
        self.assertTrue(result[0]["is_local"])


class TestIsBetterStub(unittest.TestCase):
    def test_new_higher_rank_wins(self):
        self.assertTrue(_is_better_stub({"type": "builtin"}, {"type": "module"}))

    def test_new_lower_rank_loses(self):
        self.assertFalse(_is_better_stub({"type": "module"}, {"type": "builtin"}))

    def test_equal_rank_does_not_replace(self):
        self.assertFalse(
            _is_better_stub({"type": "external"}, {"type": "imported_local"})
        )

    def test_missing_type_on_new_defaults_to_zero(self):
        self.assertFalse(_is_better_stub({}, {"type": "unresolved"}))

    def test_missing_type_on_existing_defaults_to_zero(self):
        self.assertTrue(_is_better_stub({"type": "builtin"}, {}))


if __name__ == "__main__":
    unittest.main()
