"""Direct unit coverage for small pure string/classification helpers in
analyst.languages.javascript that previously had no dedicated test — only
exercised indirectly through full-file JavaScriptAnalyzer.analyze_file
integration tests.

_strip_string_quotes strips matching quote pairs from a raw source-text
token; _is_local_module classifies an import/require specifier as local
(same-project) vs. external (node_modules), which drives cross-file edge
resolution in the call graph.
"""

import unittest

from analyst.languages.javascript import _is_local_module, _strip_string_quotes


class TestStripStringQuotes(unittest.TestCase):
    def test_strips_single_quotes(self):
        self.assertEqual(_strip_string_quotes("'hello'"), "hello")

    def test_strips_double_quotes(self):
        self.assertEqual(_strip_string_quotes('"hello"'), "hello")

    def test_strips_backticks(self):
        self.assertEqual(_strip_string_quotes("`hello`"), "hello")

    def test_strips_surrounding_whitespace_first(self):
        self.assertEqual(_strip_string_quotes("  'hello'  "), "hello")

    def test_mismatched_quotes_are_left_untouched(self):
        self.assertEqual(_strip_string_quotes("'hello\""), "'hello\"")

    def test_unquoted_string_is_left_untouched(self):
        self.assertEqual(_strip_string_quotes("hello"), "hello")

    def test_empty_string_is_left_untouched(self):
        self.assertEqual(_strip_string_quotes(""), "")

    def test_single_quote_character_is_left_untouched(self):
        # len < 2, so the quote-pair check should not index out of bounds.
        self.assertEqual(_strip_string_quotes("'"), "'")

    def test_empty_quoted_string_becomes_empty(self):
        self.assertEqual(_strip_string_quotes("''"), "")


class TestIsLocalModule(unittest.TestCase):
    def test_relative_dot_slash_is_local(self):
        self.assertTrue(_is_local_module("./foo", frozenset()))

    def test_relative_dot_dot_slash_is_local(self):
        self.assertTrue(_is_local_module("../foo/bar", frozenset()))

    def test_absolute_slash_path_is_local(self):
        self.assertTrue(_is_local_module("/src/foo", frozenset()))

    def test_top_level_segment_in_local_modules_is_local(self):
        self.assertTrue(
            _is_local_module("components/Button", frozenset({"components"}))
        )

    def test_exact_match_in_local_modules_is_local(self):
        self.assertTrue(_is_local_module("utils", frozenset({"utils"})))

    def test_bare_package_not_in_local_modules_is_external(self):
        self.assertFalse(_is_local_module("react", frozenset({"components", "utils"})))

    def test_scoped_package_not_in_local_modules_is_external(self):
        self.assertFalse(_is_local_module("@scope/pkg", frozenset()))

    def test_empty_local_modules_set_never_matches_bare_names(self):
        self.assertFalse(_is_local_module("lodash", frozenset()))


if __name__ == "__main__":
    unittest.main()
