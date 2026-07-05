"""Direct unit tests for teacher.contract — the pure normalization layer
between raw LLM output and the UI-facing teacher contract. No existing test
file covered this module before.
"""

from teacher.contract import (
    CHAT_SECTION_ORDER,
    UNKNOWN_SENTINEL,
    TeacherReferences,
    build_chat_user_prompt,
    build_contract_system_prompt,
    build_explain_user_prompt,
    build_ghost_user_prompt,
    build_refine_learning_user_prompt,
    build_suggest_learning_user_prompt,
    clip_text,
    extract_node_ids_from_summary,
    normalize_chat_text,
    normalize_explain_payload,
    normalize_ghost_payload,
    normalize_learning_steps,
    render_contract_text,
)
from teacher.contract import _extract_sections_from_text, _normalize_contract_sections


# --- TeacherReferences.render -------------------------------------------------


def test_references_render_uses_sentinel_when_empty():
    refs = TeacherReferences()
    text = refs.render()
    assert "Selected node: unknown_node" in text
    assert text.count(UNKNOWN_SENTINEL) == 4  # file_path, callers, callees, neighbors


def test_references_render_lists_known_values():
    refs = TeacherReferences(
        node_id="main",
        file_path="src/main.py",
        callers=["a", "b"],
        callees=["c"],
        neighbors=[],
    )
    text = refs.render()
    assert "Selected node: main" in text
    assert "File path: src/main.py" in text
    assert "Callers: a, b" in text
    assert "Callees: c" in text
    assert f"Neighbors: {UNKNOWN_SENTINEL}" in text


# --- clip_text -----------------------------------------------------------


def test_clip_text_returns_fallback_for_empty_or_blank():
    assert clip_text("", 10) == UNKNOWN_SENTINEL
    assert clip_text("   ", 10) == UNKNOWN_SENTINEL
    assert clip_text(None, 10, fallback="custom") == "custom"


def test_clip_text_leaves_short_text_untouched():
    assert clip_text("hello", 10) == "hello"


def test_clip_text_truncates_long_text_with_ellipsis():
    result = clip_text("abcdefghij", 5)
    assert result == "abcd…"
    assert len(result) == 5


# --- _extract_sections_from_text ------------------------------------------


def test_extract_sections_from_text_splits_on_known_headers():
    text = "What it is\nDoes a thing.\nCommon bugs\nOff-by-one errors."
    sections = _extract_sections_from_text(text)
    assert sections["What it is"] == "Does a thing."
    assert sections["Common bugs"] == "Off-by-one errors."


def test_extract_sections_from_text_ignores_preamble_before_first_header():
    text = "some noise\nWhat it is\nActual content"
    sections = _extract_sections_from_text(text)
    assert sections == {"What it is": "Actual content"}


def test_extract_sections_from_text_returns_empty_for_unrecognized_text():
    assert _extract_sections_from_text("just some free text") == {}


# --- _normalize_contract_sections / render_contract_text ------------------


def test_normalize_contract_sections_fills_all_sections_from_payload():
    refs = TeacherReferences(node_id="n1")
    parsed = {
        "sections": {"What it is": "It parses input."},
        "unknowns": ["missing docstring", ""],
    }
    section_map = _normalize_contract_sections(parsed, refs)
    assert section_map["What it is"] == "It parses input."
    assert section_map["Unknowns"] == "missing docstring"
    assert section_map["References"] == refs.render()
    for section in CHAT_SECTION_ORDER:
        assert section in section_map


def test_normalize_contract_sections_falls_back_when_sections_not_a_dict():
    refs = TeacherReferences(node_id="n1")
    section_map = _normalize_contract_sections({"sections": "oops"}, refs)
    assert section_map["What it is"] == UNKNOWN_SENTINEL


def test_render_contract_text_orders_sections_and_uses_headers():
    section_map = {section: f"body-{section}" for section in CHAT_SECTION_ORDER}
    text = render_contract_text(section_map)
    order_positions = [text.index(f"### {section}") for section in CHAT_SECTION_ORDER]
    assert order_positions == sorted(order_positions)


# --- normalize_chat_text ---------------------------------------------------


def test_normalize_chat_text_parses_valid_json_payload():
    refs = TeacherReferences(node_id="n1")
    raw = '{"sections": {"What it is": "A parser."}, "unknowns": []}'
    text = normalize_chat_text(raw, refs)
    assert "### What it is\nA parser." in text
    assert "### References" in text


def test_normalize_chat_text_falls_back_to_text_extraction_on_invalid_json():
    refs = TeacherReferences(node_id="n1")
    raw = "What it is\nA plain-text answer."
    text = normalize_chat_text(raw, refs)
    assert "### What it is\nA plain-text answer." in text
    assert f"### Unknowns\n{UNKNOWN_SENTINEL}" in text


def test_normalize_chat_text_uses_raw_text_as_what_it_is_when_no_sections_found():
    refs = TeacherReferences(node_id="n1")
    text = normalize_chat_text("totally unstructured reply", refs)
    assert "### What it is\ntotally unstructured reply" in text


# --- normalize_explain_payload ---------------------------------------------


def test_normalize_explain_payload_builds_analogy_and_takeaway():
    refs = TeacherReferences(node_id="n1")
    parsed = {"analogy": "like a filter", "key_takeaway": "keep it simple"}
    result = normalize_explain_payload(parsed, refs)
    assert result["analogy"] == "like a filter"
    assert result["key_takeaway"] == "keep it simple"
    assert "### References" in result["technical"]


def test_normalize_explain_payload_prepends_technical_details_block():
    refs = TeacherReferences(node_id="n1")
    parsed = {"technical": {"complexity": "O(n)"}}
    result = normalize_explain_payload(parsed, refs)
    assert result["technical"].startswith("### Technical Details\n")
    assert "Complexity" in result["technical"]


# --- normalize_ghost_payload ------------------------------------------------


def test_normalize_ghost_payload_defaults_invalid_importance_to_medium():
    refs = TeacherReferences(node_id="n1")
    result = normalize_ghost_payload({"importance": "critical"}, refs)
    assert result["importance"] == "medium"


def test_normalize_ghost_payload_accepts_known_importance_values():
    refs = TeacherReferences(node_id="n1")
    result = normalize_ghost_payload({"importance": "HIGH"}, refs)
    assert result["importance"] == "high"


def test_normalize_ghost_payload_falls_back_relationship_to_references():
    refs = TeacherReferences(node_id="n1", callers=["a"])
    result = normalize_ghost_payload({}, refs)
    assert result["relationship"] == refs.render()


# --- normalize_learning_steps ------------------------------------------------


def test_normalize_learning_steps_filters_disallowed_and_duplicate_nodes():
    steps = [
        {"node_id": "a", "reason": "first"},
        {"node_id": "b", "reason": "not allowed"},
        {"node_id": "a", "reason": "duplicate"},
        {"node_id": "", "reason": "blank id"},
        "not-a-dict",
    ]
    result = normalize_learning_steps(
        steps, allowed_node_ids=["a"], include_step_numbers=False
    )
    assert len(result) == 1
    assert result[0]["node_id"] == "a"
    assert result[0]["reason"] == "first"


def test_normalize_learning_steps_returns_empty_for_non_list_input():
    assert normalize_learning_steps("nope", allowed_node_ids=None, include_step_numbers=False) == []


def test_normalize_learning_steps_renumbers_when_include_step_numbers():
    steps = [{"node_id": "a"}, {"node_id": "b"}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=True)
    assert [item["step"] for item in result] == [1, 2]


def test_normalize_learning_steps_allows_all_when_no_allowlist():
    steps = [{"node_id": "x"}, {"node_id": "y"}]
    result = normalize_learning_steps(steps, allowed_node_ids=None, include_step_numbers=False)
    assert [item["node_id"] for item in result] == ["x", "y"]


# --- prompt builders --------------------------------------------------------


def test_build_contract_system_prompt_includes_mode():
    assert "Mode: explain." in build_contract_system_prompt("explain")


def test_build_explain_user_prompt_includes_code_and_context():
    refs = TeacherReferences(node_id="n1")
    prompt = build_explain_user_prompt(
        code_snippet="def f(): pass",
        level_tone="beginner",
        context="a demo repo",
        references=refs,
    )
    assert "def f(): pass" in prompt
    assert "Context: a demo repo" in prompt
    assert "Target Audience: beginner" in prompt


def test_build_explain_user_prompt_omits_context_line_when_blank():
    refs = TeacherReferences(node_id="n1")
    prompt = build_explain_user_prompt(
        code_snippet="pass", level_tone="beginner", context="", references=refs
    )
    assert "Context:" not in prompt


def test_build_chat_user_prompt_includes_question():
    refs = TeacherReferences(node_id="n1")
    prompt = build_chat_user_prompt(
        code_snippet="pass",
        question="why does this exist?",
        project_context="",
        references=refs,
    )
    assert "User question: why does this exist?" in prompt
    assert "Project Context:" not in prompt


def test_build_ghost_user_prompt_includes_transition_and_edge_context():
    refs = TeacherReferences(node_id="n1")
    prompt = build_ghost_user_prompt(
        transition="A -> B", edge_context="calls", code_snippet="pass", references=refs
    )
    assert "A -> B" in prompt
    assert "Edge context: calls" in prompt


def test_build_refine_learning_user_prompt_embeds_json_payloads():
    prompt = build_refine_learning_user_prompt(
        slim_steps=[{"node_id": "a"}], allowed_node_ids=["a", "b"]
    )
    assert '"a"' in prompt
    assert "allowed_node_ids" in prompt


def test_build_suggest_learning_user_prompt_omits_allowed_line_when_none():
    prompt = build_suggest_learning_user_prompt(
        nodes_summary="a, b",
        edges_summary="a->b",
        file_path="src/x.py",
        allowed_node_ids=None,
    )
    assert "allowed_node_ids" not in prompt
    assert "File: src/x.py" in prompt


# --- extract_node_ids_from_summary ------------------------------------------


def test_extract_node_ids_from_summary_parses_comma_separated_tokens():
    result = extract_node_ids_from_summary("main (function), helper(loc=4), , util")
    assert result == ["main", "helper", "util"]


def test_extract_node_ids_from_summary_stops_id_at_first_whitespace_or_paren():
    result = extract_node_ids_from_summary("main (entry point)")
    assert result == ["main"]


def test_extract_node_ids_from_summary_returns_empty_for_blank_input():
    assert extract_node_ids_from_summary("") == []
