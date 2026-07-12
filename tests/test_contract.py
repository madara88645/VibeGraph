"""Tests for teacher/contract.py — pure normalization/formatting helpers."""

import pytest

from teacher.contract import (
    CHAT_SECTION_ORDER,
    EXPLAIN_BUDGETS,
    GHOST_BUDGETS,
    LEARNING_REASON_BUDGET,
    SECTION_BUDGETS,
    UNKNOWN_SENTINEL,
    TeacherReferences,
    _normalize_contract_sections,
    clip_text,
    extract_node_ids_from_summary,
    normalize_chat_text,
    normalize_explain_payload,
    normalize_ghost_payload,
    normalize_learning_steps,
    render_contract_text,
)


def _refs(**kwargs) -> TeacherReferences:
    defaults = dict(node_id="foo.bar", file_path="foo.py")
    defaults.update(kwargs)
    return TeacherReferences(**defaults)


# ---------------------------------------------------------------------------
# clip_text
# ---------------------------------------------------------------------------
class TestClipText:
    def test_under_limit_returned_unchanged(self):
        assert clip_text("hello", 20) == "hello"

    def test_exactly_at_limit_returned_unchanged(self):
        text = "x" * 10
        assert clip_text(text, 10) == text

    def test_over_limit_is_truncated_with_ellipsis(self):
        text = "x" * 15
        result = clip_text(text, 10)
        assert result.endswith("…")
        # max_chars - 1 chars of content, plus the ellipsis char.
        assert len(result) == 10
        assert result == "x" * 9 + "…"

    def test_empty_string_returns_fallback(self):
        assert clip_text("", 10) == UNKNOWN_SENTINEL

    def test_whitespace_only_returns_fallback(self):
        assert clip_text("   \n\t  ", 10) == UNKNOWN_SENTINEL

    def test_none_like_falsy_value_returns_fallback(self):
        # `value or ""` in the implementation means clip_text tolerates
        # falsy non-str inputs the same way as an empty string.
        assert clip_text(None, 10) == UNKNOWN_SENTINEL  # type: ignore[arg-type]

    def test_custom_fallback_is_used(self):
        assert clip_text("", 10, fallback="N/A") == "N/A"

    def test_strips_surrounding_whitespace_before_measuring(self):
        assert clip_text("  hi  ", 10) == "hi"

    def test_truncation_strips_trailing_whitespace_before_ellipsis(self):
        text = "hello      world"
        result = clip_text(text, 8)
        # text[:7] == "hello  " -> rstrip -> "hello" + "…"
        assert result == "hello…"


# ---------------------------------------------------------------------------
# _normalize_contract_sections
# ---------------------------------------------------------------------------
class TestNormalizeContractSections:
    def test_well_formed_sections_pass_through(self):
        parsed = {
            "sections": {
                "What it is": "A widget factory.",
                "Inputs/Outputs": "Takes a config, returns a Widget.",
                "Side effects": "None.",
                "Why this node exists": "Central creation point.",
                "Common bugs": "None known.",
                "References": "See callers.",
            },
            "unknowns": ["max retries"],
        }
        result = _normalize_contract_sections(parsed, _refs())
        assert result["What it is"] == "A widget factory."
        assert result["Inputs/Outputs"] == "Takes a config, returns a Widget."
        assert result["Side effects"] == "None."
        assert result["Why this node exists"] == "Central creation point."
        assert result["Common bugs"] == "None known."
        # References from the payload wins over the auto-rendered fallback.
        assert result["References"] == "See callers."
        # Non-empty unknowns list is joined into a single comma string.
        assert result["Unknowns"] == "max retries"
        assert set(result.keys()) == set(CHAT_SECTION_ORDER)

    def test_missing_sections_key_falls_back_to_empty_per_section(self):
        parsed = {}
        refs = _refs()
        result = _normalize_contract_sections(parsed, refs)
        # Every section still present, using clip_text's fallback for the
        # empty string, EXCEPT References (defaults to refs.render()) and
        # Unknowns (defaults to UNKNOWN_SENTINEL).
        for section in CHAT_SECTION_ORDER:
            if section in ("References", "Unknowns"):
                continue
            assert result[section] == UNKNOWN_SENTINEL
        assert result["References"] == refs.render()
        assert result["Unknowns"] == UNKNOWN_SENTINEL

    def test_sections_payload_wrong_type_is_ignored(self):
        # `sections` is a string instead of a dict -> treated as {}.
        parsed = {"sections": "not a dict", "unknowns": None}
        result = _normalize_contract_sections(parsed, _refs())
        assert result["What it is"] == UNKNOWN_SENTINEL

    def test_unknowns_wrong_type_falls_back_to_sections_unknowns_field(self):
        parsed = {
            "sections": {"Unknowns": "some raw unknowns text"},
            "unknowns": "not a list",
        }
        result = _normalize_contract_sections(parsed, _refs())
        assert result["Unknowns"] == "some raw unknowns text"

    def test_unknowns_list_with_only_falsy_items_falls_back_to_sentinel(self):
        parsed = {"sections": {}, "unknowns": ["", "  ", ""]}
        result = _normalize_contract_sections(parsed, _refs())
        # join of blank strings after strip() produces "", which clip_text
        # then maps to the fallback sentinel because it's empty.
        assert result["Unknowns"] == UNKNOWN_SENTINEL

    def test_non_string_section_values_are_rendered(self):
        parsed = {
            "sections": {
                "What it is": {"summary": "a thing", "kind": "util"},
                "Inputs/Outputs": ["a", "b", 3],
            }
        }
        result = _normalize_contract_sections(parsed, _refs())
        assert "**Summary**: a thing" in result["What it is"]
        assert "**Kind**: util" in result["What it is"]
        assert result["Inputs/Outputs"] == "a, b, 3"

    def test_references_missing_uses_rendered_references_fallback(self):
        refs = _refs(node_id="my.node", file_path=None, callers=["a"])
        result = _normalize_contract_sections({"sections": {}}, refs)
        assert result["References"] == refs.render()
        assert "my.node" in result["References"]
        assert UNKNOWN_SENTINEL in result["References"]  # file_path unknown


# ---------------------------------------------------------------------------
# render_contract_text
# ---------------------------------------------------------------------------
class TestRenderContractText:
    def test_renders_all_sections_in_order_with_headers(self):
        section_map = {s: f"body-{i}" for i, s in enumerate(CHAT_SECTION_ORDER)}
        rendered = render_contract_text(section_map)
        lines = rendered.split("\n\n")
        assert len(lines) == len(CHAT_SECTION_ORDER)
        for section, block in zip(CHAT_SECTION_ORDER, lines):
            assert block.startswith(f"### {section}\n")

    def test_missing_section_in_map_renders_fallback(self):
        rendered = render_contract_text({})
        assert f"### {CHAT_SECTION_ORDER[0]}\n{UNKNOWN_SENTINEL}" in rendered


# ---------------------------------------------------------------------------
# normalize_chat_text
# ---------------------------------------------------------------------------
class TestNormalizeChatText:
    def test_valid_json_payload_is_normalized(self):
        raw = (
            '{"sections": {"What it is": "It parses stuff."}, '
            '"unknowns": ["retry count"]}'
        )
        result = normalize_chat_text(raw, _refs())
        assert "### What it is\nIt parses stuff." in result
        assert "### Unknowns\nretry count" in result

    def test_non_json_text_falls_back_to_section_extraction(self):
        # Section headers must be on their own line: `_extract_sections_from_text`
        # only starts buffering content on the lines *after* a header line
        # matches — text appended after a colon on the header's own line is
        # dropped (the header line itself is never added to the buffer).
        raw = "What it is\nparses config files.\nSide effects\nwrites a log line."
        result = normalize_chat_text(raw, _refs())
        assert "### What it is\nparses config files." in result
        assert "### Side effects\nwrites a log line." in result
        # References/Unknowns are always overwritten in the text-fallback path.
        assert "### References\n" in result
        assert f"### Unknowns\n{UNKNOWN_SENTINEL}" in result

    def test_inline_content_after_header_on_same_line_is_dropped(self):
        # Documents the nuance above from the opposite angle: content typed
        # on the same line as the header (after a colon) never makes it into
        # the section body, because the header line itself isn't buffered.
        raw = "What it is: parses config files.\nSide effects: writes a log line."
        result = normalize_chat_text(raw, _refs())
        assert f"### What it is\n{UNKNOWN_SENTINEL}" in result
        assert f"### Side effects\n{UNKNOWN_SENTINEL}" in result

    def test_plain_text_with_no_recognizable_sections_becomes_what_it_is(self):
        raw = "Just a raw sentence with no section headers at all."
        result = normalize_chat_text(raw, _refs())
        assert (
            "### What it is\nJust a raw sentence with no section headers at all."
            in result
        )

    def test_json_array_is_treated_as_non_dict_and_falls_back_to_text(self):
        raw = '["not", "a", "dict"]'
        result = normalize_chat_text(raw, _refs())
        # json.loads succeeds but isinstance(parsed, dict) is False, so it
        # falls through to _extract_sections_from_text on the raw string.
        assert "### What it is\n" in result


# ---------------------------------------------------------------------------
# normalize_explain_payload
# ---------------------------------------------------------------------------
class TestNormalizeExplainPayload:
    def test_valid_payload(self):
        parsed = {
            "analogy": "Like a mail sorter.",
            "key_takeaway": "Routes messages by type.",
            "sections": {"What it is": "A router."},
        }
        result = normalize_explain_payload(parsed, _refs())
        assert result["analogy"] == "Like a mail sorter."
        assert result["key_takeaway"] == "Routes messages by type."
        assert "### What it is\nA router." in result["technical"]

    def test_missing_keys_use_fallback_sentinel(self):
        result = normalize_explain_payload({}, _refs())
        assert result["analogy"] == UNKNOWN_SENTINEL
        assert result["key_takeaway"] == UNKNOWN_SENTINEL

    def test_wrong_type_analogy_is_coerced_to_string(self):
        parsed = {"analogy": 12345, "key_takeaway": None}
        result = normalize_explain_payload(parsed, _refs())
        assert result["analogy"] == "12345"
        assert result["key_takeaway"] == UNKNOWN_SENTINEL

    def test_technical_dict_payload_is_prepended_as_detail_block(self):
        parsed = {
            "technical": {"complexity": "O(n)"},
            "sections": {"What it is": "A sorter."},
        }
        result = normalize_explain_payload(parsed, _refs())
        assert result["technical"].startswith("### Technical Details\n")
        assert "**Complexity**: O(n)" in result["technical"]
        assert "### What it is\nA sorter." in result["technical"]

    def test_empty_technical_dict_is_not_prepended(self):
        parsed = {"technical": {}, "sections": {"What it is": "A sorter."}}
        result = normalize_explain_payload(parsed, _refs())
        assert not result["technical"].startswith("### Technical Details\n")

    def test_technical_scalar_is_ignored_as_detail_block(self):
        parsed = {"technical": "just a string", "sections": {}}
        result = normalize_explain_payload(parsed, _refs())
        assert not result["technical"].startswith("### Technical Details\n")


# ---------------------------------------------------------------------------
# normalize_ghost_payload
# ---------------------------------------------------------------------------
class TestNormalizeGhostPayload:
    def test_valid_payload(self):
        parsed = {
            "narration": "Calls the parser next.",
            "relationship": "caller -> callee",
            "importance": "high",
        }
        result = normalize_ghost_payload(parsed, _refs())
        assert result["narration"] == "Calls the parser next."
        assert result["relationship"] == "caller -> callee"
        assert result["importance"] == "high"

    def test_missing_keys_use_defaults(self):
        refs = _refs()
        result = normalize_ghost_payload({}, refs)
        assert result["narration"] == UNKNOWN_SENTINEL
        # relationship falls back to refs.render(), but is still run through
        # clip_text at GHOST_BUDGETS["relationship"] (180 chars) — the full
        # rendered references block is longer than that, so it comes back
        # truncated rather than byte-for-byte equal to refs.render().
        assert result["relationship"] == clip_text(
            refs.render(), GHOST_BUDGETS["relationship"], fallback=refs.render()
        )
        assert result["relationship"].startswith("Selected node: foo.bar")
        assert result["relationship"].endswith("…")
        assert result["importance"] == "medium"

    def test_invalid_importance_falls_back_to_medium(self):
        parsed = {"importance": "critical"}
        result = normalize_ghost_payload(parsed, _refs())
        assert result["importance"] == "medium"

    def test_importance_is_case_and_whitespace_normalized(self):
        parsed = {"importance": "  HIGH  "}
        result = normalize_ghost_payload(parsed, _refs())
        assert result["importance"] == "high"

    def test_wrong_type_importance_falls_back_to_medium(self):
        parsed = {"importance": 3}
        result = normalize_ghost_payload(parsed, _refs())
        assert result["importance"] == "medium"


# ---------------------------------------------------------------------------
# normalize_learning_steps
# ---------------------------------------------------------------------------
class TestNormalizeLearningSteps:
    def test_valid_payload_with_step_numbers(self):
        steps = [
            {"node_id": "a", "reason": "start here", "step": 5},
            {"node_id": "b", "reason": "then here"},
        ]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=True
        )
        assert [s["node_id"] for s in result] == ["a", "b"]
        # step numbers are renumbered sequentially regardless of input step.
        assert [s["step"] for s in result] == [1, 2]

    def test_step_numbers_omitted_when_not_requested(self):
        steps = [{"node_id": "a", "reason": "x"}]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=False
        )
        assert result == [{"node_id": "a", "reason": "x"}]
        assert "step" not in result[0]

    def test_wrong_type_steps_returns_empty_list(self):
        assert (
            normalize_learning_steps(
                "not a list", allowed_node_ids=None, include_step_numbers=True
            )
            == []
        )
        assert (
            normalize_learning_steps(
                None, allowed_node_ids=None, include_step_numbers=True
            )
            == []
        )
        assert (
            normalize_learning_steps(
                {"node_id": "a"}, allowed_node_ids=None, include_step_numbers=True
            )
            == []
        )

    def test_missing_node_id_is_skipped(self):
        steps = [{"reason": "no id here"}, {"node_id": "", "reason": "blank id"}]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=False
        )
        assert result == []

    def test_non_dict_items_are_skipped(self):
        steps = ["not-a-dict", {"node_id": "a", "reason": "ok"}]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=False
        )
        assert [s["node_id"] for s in result] == ["a"]

    def test_node_id_not_in_allowed_list_is_dropped(self):
        steps = [
            {"node_id": "allowed_one", "reason": "keep"},
            {"node_id": "disallowed", "reason": "drop"},
        ]
        result = normalize_learning_steps(
            steps, allowed_node_ids=["allowed_one"], include_step_numbers=False
        )
        assert [s["node_id"] for s in result] == ["allowed_one"]

    def test_empty_allowed_list_means_no_filtering(self):
        # `allowed = set(allowed_node_ids or [])`; an empty/None list means
        # the truthiness check `if allowed and node_id not in allowed` never
        # filters anything out.
        steps = [{"node_id": "anything", "reason": "keep"}]
        result = normalize_learning_steps(
            steps, allowed_node_ids=[], include_step_numbers=False
        )
        assert [s["node_id"] for s in result] == ["anything"]

    def test_duplicate_node_ids_deduplicated_keeping_first(self):
        steps = [
            {"node_id": "a", "reason": "first"},
            {"node_id": "a", "reason": "second (dup)"},
        ]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=False
        )
        assert len(result) == 1
        assert result[0]["reason"] == "first"

    def test_node_id_is_stripped_of_whitespace(self):
        steps = [{"node_id": "  spaced_id  ", "reason": "x"}]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=False
        )
        assert result[0]["node_id"] == "spaced_id"

    def test_non_positive_step_value_falls_back_to_index(self):
        steps = [{"node_id": "a", "reason": "x", "step": -1}]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=True
        )
        assert result[0]["step"] == 1

    def test_non_int_step_value_falls_back_to_index(self):
        steps = [{"node_id": "a", "reason": "x", "step": "not-an-int"}]
        result = normalize_learning_steps(
            steps, allowed_node_ids=None, include_step_numbers=True
        )
        assert result[0]["step"] == 1


# ---------------------------------------------------------------------------
# extract_node_ids_from_summary
# ---------------------------------------------------------------------------
class TestExtractNodeIdsFromSummary:
    def test_ids_present_comma_separated(self):
        summary = "foo.bar, baz.qux, module:index"
        assert extract_node_ids_from_summary(summary) == [
            "foo.bar",
            "baz.qux",
            "module:index",
        ]

    def test_ids_with_trailing_annotations_are_stripped(self):
        summary = "foo.bar (function), baz.qux (class)"
        assert extract_node_ids_from_summary(summary) == ["foo.bar", "baz.qux"]

    def test_absent_ids_empty_string_returns_empty_list(self):
        assert extract_node_ids_from_summary("") == []

    def test_mixed_blank_and_valid_tokens(self):
        summary = "foo.bar, , baz.qux,   "
        assert extract_node_ids_from_summary(summary) == ["foo.bar", "baz.qux"]

    def test_single_id_without_commas(self):
        assert extract_node_ids_from_summary("solo_node") == ["solo_node"]


# ---------------------------------------------------------------------------
# TeacherReferences.render
# ---------------------------------------------------------------------------
class TestTeacherReferencesRender:
    def test_render_with_all_fields_populated(self):
        refs = TeacherReferences(
            node_id="mod.fn",
            file_path="mod.py",
            callers=["a", "b"],
            callees=["c"],
            neighbors=["d", "e"],
        )
        rendered = refs.render()
        assert "Selected node: mod.fn" in rendered
        assert "File path: mod.py" in rendered
        assert "Callers: a, b" in rendered
        assert "Callees: c" in rendered
        assert "Neighbors: d, e" in rendered

    def test_render_with_defaults_uses_unknown_sentinel(self):
        refs = TeacherReferences()
        rendered = refs.render()
        assert "Selected node: unknown_node" in rendered
        assert f"File path: {UNKNOWN_SENTINEL}" in rendered
        assert f"Callers: {UNKNOWN_SENTINEL}" in rendered
        assert f"Callees: {UNKNOWN_SENTINEL}" in rendered
        assert f"Neighbors: {UNKNOWN_SENTINEL}" in rendered


# ---------------------------------------------------------------------------
# Sanity check on budgets used above (documents real constants, not guesses)
# ---------------------------------------------------------------------------
class TestBudgetsAreDefinedForEverySection:
    def test_section_budgets_cover_all_chat_sections(self):
        assert set(SECTION_BUDGETS.keys()) == set(CHAT_SECTION_ORDER)

    def test_explain_and_ghost_budgets_are_positive_ints(self):
        for budget in {**EXPLAIN_BUDGETS, **GHOST_BUDGETS}.values():
            assert isinstance(budget, int)
            assert budget > 0
        assert isinstance(LEARNING_REASON_BUDGET, int)
        assert LEARNING_REASON_BUDGET > 0


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
