"""Direct unit coverage for pure AST-parsing helpers in
analyst.languages.javascript and analyst.languages.python that had no
dedicated test — a follow-up to test_javascript_parsing_helpers.py, which
already covers _Walker._classify_call, _parse_import_statement, and
_parse_require_call. This file is scoped to the remaining gap identified
by audit:

  * javascript.py: _Walker._collect_immediate_metadata (pure tree-sitter
    node -> (calls: set, side_effect: bool)), _Walker._max_nesting_depth
    (JS-specific nesting-depth walk, a separate implementation from the
    Python analyzer's), and module-level _node_text.
  * python.py: attach_language_to_node_payload (idempotent
    dict.setdefault("language", ...) helper) and
    PythonAnalyzer.is_top_level_entry_name (trivial membership check).

A bug in any of these silently mis-computes per-definition graph metadata
(dependency_count, side_effect_boundary, nesting_depth) or entry-point /
language tagging without raising an error.
"""

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from analyst.languages.javascript import _Walker, _node_text
from analyst.languages.python import PythonAnalyzer, attach_language_to_node_payload
from analyst.tree_sitter_loader import get_parser


def _parse(source: str):
    parser = get_parser("javascript")
    return parser.parse(source.encode("utf-8"))


def _find_first(node, node_type: str):
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type == node_type:
            return current
        stack.extend(reversed(current.children))
    return None


def _walker(source: str) -> _Walker:
    return _Walker(
        file_path="<test>", source=source.encode("utf-8"), language_id="javascript"
    )


def _function_body(source: str):
    tree = _parse(source)
    fn = _find_first(tree.root_node, "function_declaration")
    return fn.child_by_field_name("body")


class TestNodeText(unittest.TestCase):
    def test_extracts_exact_slice(self):
        source = "const foo = 1;"
        tree = _parse(source)
        node = _find_first(tree.root_node, "identifier")
        self.assertEqual(_node_text(node, source.encode("utf-8")), "foo")

    def test_whole_program_slice_round_trips(self):
        source = "function f() { return 1; }"
        tree = _parse(source)
        self.assertEqual(
            _node_text(tree.root_node, source.encode("utf-8")), source
        )

    def test_decodes_non_utf8_bytes_with_replace_rather_than_raising(self):
        # A node text helper used across a whole file must never raise on
        # decode — malformed bytes should be replaced, not blow up parsing.
        source_bytes = b"const foo = 1;"
        tree = get_parser("javascript").parse(source_bytes)
        node = _find_first(tree.root_node, "identifier")
        # Splice in an invalid UTF-8 byte inside the slice range artificially
        # by re-decoding a byte string that contains one.
        bad_bytes = b"\xff\xfe"
        result = _node_text(
            type("N", (), {"start_byte": 0, "end_byte": len(bad_bytes)})(), bad_bytes
        )
        self.assertIsInstance(result, str)
        # errors="replace" substitutes U+FFFD rather than raising.
        self.assertIn("�", result)


class TestMaxNestingDepth(unittest.TestCase):
    def test_no_nesting_is_zero(self):
        body = _function_body("function f() { return 1; }")
        self.assertEqual(_walker("")._max_nesting_depth(body), 0)

    def test_single_if_is_depth_one(self):
        body = _function_body("function f() { if (x) { return 1; } }")
        self.assertEqual(_walker("")._max_nesting_depth(body), 1)

    def test_nested_if_inside_for_is_depth_two(self):
        source = "function f() { for (;;) { if (x) { return 1; } } }"
        body = _function_body(source)
        self.assertEqual(_walker("")._max_nesting_depth(body), 2)

    def test_triple_nested_control_flow(self):
        source = (
            "function f() { while (x) { for (;;) { try { "
            "if (y) { return 1; } } catch (e) {} } } }"
        )
        body = _function_body(source)
        self.assertEqual(_walker("")._max_nesting_depth(body), 4)

    def test_sibling_branches_do_not_add_depth(self):
        # Two sequential (not nested) if-statements should each independently
        # contribute depth 1, not accumulate to 2.
        source = "function f() { if (a) {} if (b) {} }"
        body = _function_body(source)
        self.assertEqual(_walker("")._max_nesting_depth(body), 1)

    def test_switch_and_do_while_count_as_nesting(self):
        source = "function f() { switch (x) { case 1: do { y(); } while (z); } }"
        body = _function_body(source)
        self.assertEqual(_walker("")._max_nesting_depth(body), 2)


class TestCollectImmediateMetadata(unittest.TestCase):
    def _metadata(self, source: str):
        body = _function_body(source)
        return _walker(source)._collect_immediate_metadata(body)

    def test_no_calls_no_side_effects(self):
        calls, side_effect = self._metadata("function f() { return 1; }")
        self.assertEqual(calls, set())
        self.assertFalse(side_effect)

    def test_bare_identifier_call_is_collected(self):
        calls, side_effect = self._metadata("function f() { helper(); }")
        self.assertEqual(calls, {"helper"})
        self.assertFalse(side_effect)

    def test_member_expression_call_collects_property_name_only(self):
        calls, side_effect = self._metadata("function f() { obj.method(); }")
        self.assertEqual(calls, {"method"})
        self.assertFalse(side_effect)

    def test_multiple_calls_are_unioned_into_a_set(self):
        calls, side_effect = self._metadata(
            "function f() { a(); b(); a(); obj.c(); }"
        )
        self.assertEqual(calls, {"a", "b", "c"})
        self.assertFalse(side_effect)

    def test_require_of_side_effect_module_sets_flag(self):
        calls, side_effect = self._metadata(
            'function f() { const fs = require("fs"); }'
        )
        self.assertIn("require", calls)
        self.assertTrue(side_effect)

    def test_require_of_non_side_effect_module_does_not_set_flag(self):
        calls, side_effect = self._metadata(
            'function f() { const x = require("lodash"); }'
        )
        self.assertIn("require", calls)
        self.assertFalse(side_effect)

    def test_import_of_side_effect_module_sets_flag(self):
        # import_statement nested inside a function body is unusual JS but
        # the tree-sitter grammar still parses it; the helper should still
        # detect the side-effect module by source string.
        source = 'function f() { if (x) { import "fs"; } }'
        calls, side_effect = self._metadata(source)
        self.assertTrue(side_effect)

    def test_computed_member_call_contributes_no_call_name(self):
        # obj[key]() — callee is a subscript_expression, not identifier or
        # member_expression, so nothing should be added to the call set.
        calls, side_effect = self._metadata("function f() { obj[key](); }")
        self.assertEqual(calls, set())
        self.assertFalse(side_effect)


class TestAttachLanguageToNodePayload(unittest.TestCase):
    def test_sets_language_when_absent(self):
        payload = {"type": "function"}
        result = attach_language_to_node_payload(payload)
        self.assertEqual(result["language"], "python")

    def test_default_language_is_python(self):
        payload = {}
        attach_language_to_node_payload(payload)
        self.assertEqual(payload["language"], "python")

    def test_custom_language_id_is_used_when_provided(self):
        payload = {}
        attach_language_to_node_payload(payload, language_id="javascript")
        self.assertEqual(payload["language"], "javascript")

    def test_idempotent_does_not_overwrite_existing_value(self):
        payload = {"language": "typescript"}
        attach_language_to_node_payload(payload, language_id="python")
        self.assertEqual(payload["language"], "typescript")

    def test_mutates_and_returns_the_same_dict(self):
        payload = {"type": "class"}
        result = attach_language_to_node_payload(payload)
        self.assertIs(result, payload)


class TestIsTopLevelEntryName(unittest.TestCase):
    def setUp(self):
        self.analyzer = PythonAnalyzer()

    def test_main_is_entry_name(self):
        self.assertTrue(self.analyzer.is_top_level_entry_name("main"))

    def test_run_is_entry_name(self):
        self.assertTrue(self.analyzer.is_top_level_entry_name("run"))

    def test_app_is_entry_name(self):
        self.assertTrue(self.analyzer.is_top_level_entry_name("app"))

    def test_arbitrary_name_is_not_entry_name(self):
        self.assertFalse(self.analyzer.is_top_level_entry_name("helper"))

    def test_empty_string_is_not_entry_name(self):
        self.assertFalse(self.analyzer.is_top_level_entry_name(""))

    def test_is_case_sensitive(self):
        self.assertFalse(self.analyzer.is_top_level_entry_name("Main"))


if __name__ == "__main__":
    unittest.main()
