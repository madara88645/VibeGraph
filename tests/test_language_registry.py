"""Direct unit coverage for the analyst.languages plugin registry, which
previously had no dedicated test — only touched indirectly via one HTTP
test hitting /api/languages (test_mixed_language_upload.py).

get_analyzer_for_path/all_languages/all_extensions are pure lookups over a
static registry of language plugins; a bug here silently misroutes files to
the wrong analyzer or drops a supported extension without raising an error.
"""

import unittest

from analyst.languages import all_extensions, all_languages, get_analyzer_for_path
from analyst.languages.javascript import JavaScriptAnalyzer
from analyst.languages.python import PythonAnalyzer
from analyst.languages.typescript import TypeScriptAnalyzer


class TestGetAnalyzerForPath(unittest.TestCase):
    def test_python_extension_resolves_to_python_analyzer(self):
        self.assertIsInstance(get_analyzer_for_path("/proj/main.py"), PythonAnalyzer)

    def test_javascript_extensions_resolve_to_javascript_analyzer(self):
        for ext in (".js", ".jsx", ".mjs", ".cjs"):
            with self.subTest(ext=ext):
                self.assertIsInstance(
                    get_analyzer_for_path(f"/proj/file{ext}"), JavaScriptAnalyzer
                )

    def test_typescript_extensions_resolve_to_typescript_analyzer(self):
        for ext in (".ts", ".tsx"):
            with self.subTest(ext=ext):
                self.assertIsInstance(
                    get_analyzer_for_path(f"/proj/file{ext}"), TypeScriptAnalyzer
                )

    def test_extension_matching_is_case_insensitive(self):
        self.assertIsInstance(get_analyzer_for_path("/proj/MAIN.PY"), PythonAnalyzer)

    def test_unsupported_extension_returns_none(self):
        self.assertIsNone(get_analyzer_for_path("/proj/README.md"))

    def test_no_extension_returns_none(self):
        self.assertIsNone(get_analyzer_for_path("/proj/Makefile"))


class TestAllLanguages(unittest.TestCase):
    def test_returns_one_entry_per_registered_analyzer(self):
        languages = all_languages()
        ids = {entry["id"] for entry in languages}
        self.assertEqual(ids, {"python", "javascript", "typescript"})

    def test_each_entry_has_label_and_extensions(self):
        languages = all_languages()
        by_id = {entry["id"]: entry for entry in languages}
        self.assertEqual(by_id["python"]["label"], "Python")
        self.assertEqual(by_id["python"]["extensions"], [".py"])
        self.assertEqual(by_id["typescript"]["extensions"], [".ts", ".tsx"])


class TestAllExtensions(unittest.TestCase):
    def test_includes_every_registered_extension(self):
        extensions = all_extensions()
        for ext in (".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"):
            with self.subTest(ext=ext):
                self.assertIn(ext, extensions)

    def test_result_is_sorted(self):
        extensions = all_extensions()
        self.assertEqual(extensions, tuple(sorted(extensions)))

    def test_result_has_no_duplicates(self):
        extensions = all_extensions()
        self.assertEqual(len(extensions), len(set(extensions)))


if __name__ == "__main__":
    unittest.main()
