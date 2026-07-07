"""Unit tests for teacher/contract.py.

This module parses and normalizes LLM output into the structured "Vibe
Teacher" contract (chat sections, explain/ghost payloads, learning steps)
but had no dedicated test file, even though it is imported by
teacher/openrouter_teacher.py. These are pure functions with no network or
LLM calls, so they are unit-tested directly here.
"""

from teacher.contract import (
    CHAT_SECTION_ORDER,
    UNKNOWN_SENTINEL,
    TeacherReferences,
    _extract_sections_from_text,
    _normalize_contract_sections,
    clip_text,
    extract_node_ids_from_summary,
    normalize_chat_text,
    normalize_explain_payload,
    normalize_ghost_payload,
    normalize_learning_steps,
    render_contract_text,
)


# ---------------------------------------------------------------------------
# clip_text
# ---------------------------------------------------------------------------


def test_clip_text_returns_stripped_text_when_within_budget():
    assert clip_text("  hello world  ", 50) == "hello world"


def test_clip_text_returns_fallback_for_empty_or_blank_input():
    assert clip_text("", 50) == UNKNOWN_SENTINEL
    assert clip_text("   ", 50) == UNKNOWN_SENTINEL


def test_clip_text_uses_custom_fallback():
    assert clip_text("", 50, fallback="n/a") == "n/a"


def test_clip_text_truncates_with_ellipsis_when_over_budget():
    text = "a" * 20
    result = clip_text(text, 10)
    assert result.endswith("…")
    assert len(result) == 10


def test_clip_text_exact_boundary_is_not_truncated():
    text = "a" * 10
    assert clip_text(text, 10) == text


# ---------------------------------------------------------------------------
# TeacherReferences.render
# ---------------------------------------------------------------------------


def test_references_render_with_all_fields_populated():
    refs = TeacherReferences(
        node_id="foo.bar",
        file_path="foo/bar.py",
        callers=["a", "b"],
        callees=["c"],
        neighbors=["d", "e"],
    )
    rendered = refs.render()
    assert "Selected node: foo.bar" in rendered
    assert "File path: foo/bar.py" in rendered
    assert "Callers: a, b" in rendered
    assert "Callees: c" in rendered
    assert "Neighbors: d, e" in rendered


def test_references_render_falls_back_to_sentinels_when_empty():
    refs = TeacherReferences()
    rendered = refs.render()
    assert "Selected node: unknown_node" in rendered
    assert rendered.count(UNKNOWN_SENTINEL) == 4  # file_path, callers, callees, neighbors


# ---------------------------------------------------------------------------
# _extract_sections_from_text
# ---------------------------------------------------------------------------


def test_extract_sections_from_text_splits_on_known_headings():
    text = (
        "What it is\nA helper function.\n"
        "Common bugs\nOff-by-one errors.\n"
    )
    sections = _extract_sections_from_text(text)
    assert sections["What it is"] == "A helper function."
    assert sections["Common bugs"] == "Off-by-one errors."


def test_extract_sections_from_text_is_case_insensitive():
    text = "WHAT IT IS\nDoes a thing.\n"
    sections = _extract_sections_from_text(text)
    assert sections["What it is"] == "Does a thing."


def test_extract_sections_from_text_ignores_preamble_before_first_heading():
    text = "Some preamble that matches no section.\nWhat it is\nBody text.\n"
    sections = _extract_sections_from_text(text)
    assert "Some preamble" not in sections.get("What it is", "")
    assert sections["What it is"] == "Body text."


def test_extract_sections_from_text_returns_empty_dict_for_unmatched_text():
    assert _extract_sections_from_text("nothing recognizable here") == {}


# ---------------------------------------------------------------------------
# _normalize_contract_sections / render_contract_text
# ---------------------------------------------------------------------------


def test_normalize_contract_sections_uses_references_when_none_provided():
    refs = TeacherReferences(node_id="n1")
    sections = _normalize_contract_sections({}, refs)
    assert sections["References"] == refs.render()
    assert sections["Unknowns"] == UNKNOWN_SENTINEL


def test_normalize_contract_sections_prefers_explicit_unknowns_list():
    refs = TeacherReferences(node_id="n1")
    parsed = {"unknowns": ["missing return type", "missing docstring"]}
    sections = _normalize_contract_sections(parsed, refs)
    assert sections["Unknowns"] == "missing return type, missing docstring"


def test_normalize_contract_sections_renders_nested_dict_values():
    refs = TeacherReferences(node_id="n1")
    parsed = {"sections": {"What it is": {"summary": "does stuff"}}}
    sections = _normalize_contract_sections(parsed, refs)
    assert "**Summary**: does stuff" in sections["What it is"]


def test_render_contract_text_orders_sections_and_uses_headings():
    section_map = {section: f"body for {section}" for section in CHAT_SECTION_ORDER}
    rendered = render_contract_text(section_map)
    # Headings must appear in CHAT_SECTION_ORDER.
    positions = [rendered.index(f"### {s}") for s in CHAT_SECTION_ORDER]
    assert positions == sorted(positions)


# ---------------------------------------------------------------------------
# normalize_chat_text
# ---------------------------------------------------------------------------


def test_normalize_chat_text_parses_valid_json_payload():
    refs = TeacherReferences(node_id="n1")
    raw = '{"sections": {"What it is": "It parses JSON."}, "unknowns": []}'
    rendered = normalize_chat_text(raw, refs)
    assert "### What it is" in rendered
    assert "It parses JSON." in rendered


def test_normalize_chat_text_falls_back_to_text_extraction_on_invalid_json():
    refs = TeacherReferences(node_id="n1")
    raw = "What it is\nA plain text answer, not JSON."
    rendered = normalize_chat_text(raw, refs)
    assert "### What it is" in rendered
    assert "A plain text answer, not JSON." in rendered


def test_normalize_chat_text_uses_whole_text_as_what_it_is_when_no_sections_found():
    refs = TeacherReferences(node_id="n1")
    raw = "totally unstructured reply"
    rendered = normalize_chat_text(raw, refs)
    assert "### What it is" in rendered
    assert "totally unstructured reply" in rendered


def test_normalize_chat_text_always_includes_references_section():
    refs = TeacherReferences(node_id="n1", file_path="a.py")
    raw = "not json at all"
    rendered = normalize_chat_text(raw, refs)
    assert "### References" in rendered
    assert "a.py" in rendered


# ---------------------------------------------------------------------------
# normalize_explain_payload
# ---------------------------------------------------------------------------


def test_normalize_explain_payload_clips_analogy_and_takeaway():
    refs = TeacherReferences(node_id="n1")
    parsed = {"analogy": "a" * 500, "key_takeaway": "b" * 500}
    result = normalize_explain_payload(parsed, refs)
    assert len(result["analogy"]) <= 240
    assert len(result["key_takeaway"]) <= 180


def test_normalize_explain_payload_prepends_technical_details_when_present():
    refs = TeacherReferences(node_id="n1")
    parsed = {"technical": {"complexity": "O(n)"}}
    result = normalize_explain_payload(parsed, refs)
    assert result["technical"].startswith("### Technical Details")
    assert "O(n)" in result["technical"]


def test_normalize_explain_payload_omits_technical_details_when_absent():
    refs = TeacherReferences(node_id="n1")
    result = normalize_explain_payload({}, refs)
    assert not result["technical"].startswith("### Technical Details")


# ---------------------------------------------------------------------------
# normalize_ghost_payload
# ---------------------------------------------------------------------------


def test_normalize_ghost_payload_defaults_importance_to_medium():
    refs = TeacherReferences(node_id="n1")
    result = normalize_ghost_payload({}, refs)
    assert result["importance"] == "medium"


def test_normalize_ghost_payload_normalizes_case_and_rejects_invalid_values():
    refs = TeacherReferences(node_id="n1")
    assert normalize_ghost_payload({"importance": "HIGH"}, refs)["importance"] == "high"
    assert normalize_ghost_payload({"importance": "urgent"}, refs)["importance"] == "medium"


def test_normalize_ghost_payload_falls_back_relationship_to_references():
    # Keep refs.render() short enough to fit under GHOST_BUDGETS["relationship"]
    # (180 chars) -- a refs with unknown-sentinel fields would exceed the
    # budget and get truncated by clip_text, which is exercised separately.
    refs = TeacherReferences(node_id="n1", file_path="a.py", callers=["x"], callees=["y"], neighbors=["z"])
    result = normalize_ghost_payload({}, refs)
    assert result["relationship"] == refs.render()


def test_normalize_ghost_payload_truncates_long_reference_fallback():
    refs = TeacherReferences(node_id="n1")  # unknown sentinels push render() over budget
    result = normalize_ghost_payload({}, refs)
    assert len(result["relationship"]) <= 180
    assert result["relationship"].endswith("…")


# ---------------------------------------------------------------------------
# normalize_learning_steps
# ---------------------------------------------------------------------------


def test_normalize_learning_steps_returns_empty_for_non_list_input():
    assert normalize_learning_steps(None, allowed_node_ids=None, include_step_numbers=True) == []
    assert normalize_learning_steps("nope", allowed_node_ids=None, include_step_numbers=True) == []


def test_normalize_learning_steps_filters_disallowed_node_ids():
    steps = [{"node_id": "a", "reason": "r1"}, {"node_id": "b", "reason": "r2"}]
    result = normalize_learning_steps(steps, allowed_node_ids=["a"], include_step_numbers=False)
    assert [s["node_id"] for s in result] == ["a"]


def test_normalize_learning_steps_deduplicates_repeated_node_ids():
    steps = [
        {"node_id": "a", "reason": "first"},
        {"node_id": "a", "reason": "second"},
    ]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert len(result) == 1
    assert result[0]["reason"] == "first"


def test_normalize_learning_steps_skips_entries_without_node_id():
    steps = [{"reason": "no node id"}, {"node_id": "", "reason": "blank"}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert result == []


def test_normalize_learning_steps_renumbers_sequentially_when_requested():
    steps = [
        {"node_id": "a", "step": 5},
        {"node_id": "b", "step": 1},
    ]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=True)
    assert [s["step"] for s in result] == [1, 2]


def test_normalize_learning_steps_omits_step_key_when_not_requested():
    steps = [{"node_id": "a", "step": 5}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert "step" not in result[0]


# ---------------------------------------------------------------------------
# extract_node_ids_from_summary
# ---------------------------------------------------------------------------


def test_extract_node_ids_from_summary_splits_on_commas():
    assert extract_node_ids_from_summary("foo, bar, baz") == ["foo", "bar", "baz"]


def test_extract_node_ids_from_summary_strips_trailing_annotations():
    assert extract_node_ids_from_summary("foo.bar (function), baz.qux (class)") == [
        "foo.bar",
        "baz.qux",
    ]


def test_extract_node_ids_from_summary_ignores_blank_entries():
    assert extract_node_ids_from_summary("foo, , bar") == ["foo", "bar"]


def test_extract_node_ids_from_summary_handles_empty_string():
    assert extract_node_ids_from_summary("") == []
