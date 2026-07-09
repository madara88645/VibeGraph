"""Tests for teacher/contract.py — shared teacher contract normalization helpers.

These functions are pure text/dict transforms (no LLM/network/filesystem calls):
they normalize raw or LLM-produced payloads into the fixed-shape contract that
every teacher endpoint (chat/explain/ghost/learning) renders to the client.
"""

from teacher.contract import (
    CHAT_SECTION_ORDER,
    GHOST_BUDGETS,
    UNKNOWN_SENTINEL,
    TeacherReferences,
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


def test_clip_text_returns_fallback_for_empty_or_whitespace():
    assert clip_text("", 10) == UNKNOWN_SENTINEL
    assert clip_text("   \n\t  ", 10) == UNKNOWN_SENTINEL
    assert clip_text(None, 10) == UNKNOWN_SENTINEL  # type: ignore[arg-type]


def test_clip_text_uses_custom_fallback():
    assert clip_text("", 10, fallback="custom") == "custom"


def test_clip_text_strips_and_returns_short_text_unchanged():
    assert clip_text("  hello world  ", 50) == "hello world"


def test_clip_text_truncates_and_appends_ellipsis():
    text = "a" * 30
    result = clip_text(text, 10)
    assert len(result) == 10
    assert result.endswith("…")
    assert result[:-1] == "a" * 9


def test_clip_text_boundary_exact_length_not_truncated():
    text = "a" * 10
    assert clip_text(text, 10) == text


# ---------------------------------------------------------------------------
# TeacherReferences.render
# ---------------------------------------------------------------------------


def test_references_render_all_fields_present():
    refs = TeacherReferences(
        node_id="node_1",
        file_path="app/main.py",
        callers=["a", "b"],
        callees=["c"],
        neighbors=["d", "e"],
    )
    rendered = refs.render()
    assert "Selected node: node_1" in rendered
    assert "File path: app/main.py" in rendered
    assert "Callers: a, b" in rendered
    assert "Callees: c" in rendered
    assert "Neighbors: d, e" in rendered


def test_references_render_defaults_when_empty():
    refs = TeacherReferences()
    rendered = refs.render()
    assert "Selected node: unknown_node" in rendered
    assert f"File path: {UNKNOWN_SENTINEL}" in rendered
    assert f"Callers: {UNKNOWN_SENTINEL}" in rendered
    assert f"Callees: {UNKNOWN_SENTINEL}" in rendered
    assert f"Neighbors: {UNKNOWN_SENTINEL}" in rendered


# ---------------------------------------------------------------------------
# render_contract_text
# ---------------------------------------------------------------------------


def test_render_contract_text_includes_all_sections_in_order():
    section_map = {section: f"body for {section}" for section in CHAT_SECTION_ORDER}
    rendered = render_contract_text(section_map)
    positions = [rendered.index(f"### {section}") for section in CHAT_SECTION_ORDER]
    assert positions == sorted(positions)
    for section in CHAT_SECTION_ORDER:
        assert f"### {section}\nbody for {section}" in rendered


def test_render_contract_text_missing_section_renders_empty_body():
    rendered = render_contract_text({})
    for section in CHAT_SECTION_ORDER:
        assert f"### {section}\n" in rendered


# ---------------------------------------------------------------------------
# normalize_chat_text
# ---------------------------------------------------------------------------


def test_normalize_chat_text_from_valid_json_payload():
    refs = TeacherReferences(node_id="n1")
    raw = (
        '{"sections": {"What it is": "A function that adds numbers."}, '
        '"unknowns": ["return type"]}'
    )
    result = normalize_chat_text(raw, refs)
    assert "### What it is\nA function that adds numbers." in result
    assert "### Unknowns\nreturn type" in result
    assert "### References\nSelected node: n1" in result


def test_normalize_chat_text_falls_back_to_plain_text_when_not_json():
    refs = TeacherReferences(node_id="n2")
    raw = "What it is\nThis parses config files.\n\nCommon bugs\nMissing keys crash."
    result = normalize_chat_text(raw, refs)
    assert "### What it is\nThis parses config files." in result
    assert "### Common bugs\nMissing keys crash." in result
    assert "### References\nSelected node: n2" in result
    assert f"### Unknowns\n{UNKNOWN_SENTINEL}" in result


def test_normalize_chat_text_unparseable_text_falls_back_to_what_it_is():
    refs = TeacherReferences(node_id="n3")
    raw = "Just a single unlabeled paragraph with no section headers at all."
    result = normalize_chat_text(raw, refs)
    assert "### What it is\nJust a single unlabeled paragraph" in result


def test_normalize_chat_text_json_array_is_not_treated_as_dict():
    refs = TeacherReferences(node_id="n4")
    raw = '["not", "a", "dict"]'
    result = normalize_chat_text(raw, refs)
    # Falls through to the text-extraction path since parsed value isn't a dict.
    assert "### References\nSelected node: n4" in result


# ---------------------------------------------------------------------------
# normalize_explain_payload
# ---------------------------------------------------------------------------


def test_normalize_explain_payload_basic_fields():
    refs = TeacherReferences(node_id="n5")
    parsed = {
        "analogy": "Like a filing cabinet.",
        "key_takeaway": "Organizes data efficiently.",
        "sections": {"What it is": "A data store."},
    }
    result = normalize_explain_payload(parsed, refs)
    assert result["analogy"] == "Like a filing cabinet."
    assert result["key_takeaway"] == "Organizes data efficiently."
    assert "### What it is\nA data store." in result["technical"]


def test_normalize_explain_payload_clips_long_analogy():
    refs = TeacherReferences()
    parsed = {"analogy": "x" * 500, "key_takeaway": "short"}
    result = normalize_explain_payload(parsed, refs)
    assert len(result["analogy"]) == 240
    assert result["analogy"].endswith("…")


def test_normalize_explain_payload_prepends_technical_details_block():
    refs = TeacherReferences()
    parsed = {
        "analogy": "a",
        "key_takeaway": "b",
        "technical": {"complexity": "O(n)"},
    }
    result = normalize_explain_payload(parsed, refs)
    assert result["technical"].startswith("### Technical Details\n")
    assert "Complexity" in result["technical"]


def test_normalize_explain_payload_ignores_empty_technical_raw():
    refs = TeacherReferences()
    parsed = {"analogy": "a", "key_takeaway": "b", "technical": {}}
    result = normalize_explain_payload(parsed, refs)
    assert not result["technical"].startswith("### Technical Details\n")


# ---------------------------------------------------------------------------
# normalize_ghost_payload
# ---------------------------------------------------------------------------


def test_normalize_ghost_payload_valid_importance_passthrough():
    refs = TeacherReferences()
    parsed = {"importance": "HIGH", "narration": "Calls the parser.", "relationship": "calls"}
    result = normalize_ghost_payload(parsed, refs)
    assert result["importance"] == "high"
    assert result["narration"] == "Calls the parser."
    assert result["relationship"] == "calls"


def test_normalize_ghost_payload_invalid_importance_defaults_medium():
    refs = TeacherReferences()
    parsed = {"importance": "critical", "narration": "n"}
    result = normalize_ghost_payload(parsed, refs)
    assert result["importance"] == "medium"


def test_normalize_ghost_payload_missing_importance_defaults_medium():
    refs = TeacherReferences()
    parsed = {"narration": "n"}
    result = normalize_ghost_payload(parsed, refs)
    assert result["importance"] == "medium"


def test_normalize_ghost_payload_relationship_falls_back_to_references():
    refs = TeacherReferences(node_id="n6")
    parsed = {"narration": "n"}
    result = normalize_ghost_payload(parsed, refs)
    assert result["relationship"] == clip_text(
        refs.render(), GHOST_BUDGETS["relationship"], fallback=refs.render()
    )
    assert result["relationship"].startswith("Selected node: n6")


def test_normalize_ghost_payload_clips_narration_to_budget():
    refs = TeacherReferences()
    parsed = {"narration": "y" * 500}
    result = normalize_ghost_payload(parsed, refs)
    assert len(result["narration"]) == GHOST_BUDGETS["narration"]


# ---------------------------------------------------------------------------
# normalize_learning_steps
# ---------------------------------------------------------------------------


def test_normalize_learning_steps_non_list_returns_empty():
    assert normalize_learning_steps(None, allowed_node_ids=None, include_step_numbers=True) == []
    assert normalize_learning_steps("nope", allowed_node_ids=None, include_step_numbers=True) == []
    assert normalize_learning_steps({}, allowed_node_ids=None, include_step_numbers=True) == []


def test_normalize_learning_steps_filters_disallowed_nodes():
    steps = [{"node_id": "a", "reason": "r1"}, {"node_id": "b", "reason": "r2"}]
    result = normalize_learning_steps(steps, allowed_node_ids=["a"], include_step_numbers=False)
    assert [s["node_id"] for s in result] == ["a"]


def test_normalize_learning_steps_skips_missing_or_blank_node_id():
    steps = [{"reason": "no id"}, {"node_id": "  ", "reason": "blank"}, {"node_id": "ok"}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert [s["node_id"] for s in result] == ["ok"]


def test_normalize_learning_steps_deduplicates_repeated_node_ids():
    steps = [{"node_id": "a"}, {"node_id": "a"}, {"node_id": "b"}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert [s["node_id"] for s in result] == ["a", "b"]


def test_normalize_learning_steps_skips_non_dict_items():
    steps = ["not-a-dict", {"node_id": "a"}, 42]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert [s["node_id"] for s in result] == ["a"]


def test_normalize_learning_steps_renumbers_sequentially_when_requested():
    steps = [{"node_id": "a"}, {"node_id": "b"}, {"node_id": "c"}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=True)
    assert [s["step"] for s in result] == [1, 2, 3]


def test_normalize_learning_steps_omits_step_key_when_not_requested():
    steps = [{"node_id": "a", "step": 5}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert "step" not in result[0]


def test_normalize_learning_steps_clips_reason_to_budget():
    steps = [{"node_id": "a", "reason": "z" * 500}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert len(result[0]["reason"]) == 220


# ---------------------------------------------------------------------------
# extract_node_ids_from_summary
# ---------------------------------------------------------------------------


def test_extract_node_ids_from_summary_basic_comma_separated():
    summary = "node_a (file.py), node_b (other.py), node_c"
    assert extract_node_ids_from_summary(summary) == ["node_a", "node_b", "node_c"]


def test_extract_node_ids_from_summary_empty_string():
    assert extract_node_ids_from_summary("") == []


def test_extract_node_ids_from_summary_ignores_blank_segments():
    summary = "node_a, , node_b,   "
    assert extract_node_ids_from_summary(summary) == ["node_a", "node_b"]


def test_extract_node_ids_from_summary_single_entry_no_parens():
    assert extract_node_ids_from_summary("solo_node") == ["solo_node"]
