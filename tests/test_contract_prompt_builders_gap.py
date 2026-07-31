"""Tests for the prompt-builder functions in teacher/contract.py.

These pure string formatters (no I/O, no network, no LLM calls) are called
from teacher/openrouter_teacher.py, but their actual output content was
never asserted anywhere — only invoked indirectly under HTTP-response
mocking. A regression here (e.g. a dropped instruction, missing JSON-key
list, or broken references block) would go undetected by the existing
suite.
"""

from teacher.contract import (
    CHAT_SECTION_ORDER,
    TeacherReferences,
    build_chat_user_prompt,
    build_contract_system_prompt,
    build_explain_user_prompt,
    build_ghost_user_prompt,
    build_refine_learning_user_prompt,
    build_suggest_learning_user_prompt,
)


def _refs(**kwargs) -> TeacherReferences:
    defaults = dict(node_id="foo.bar", file_path="foo.py")
    defaults.update(kwargs)
    return TeacherReferences(**defaults)


# ---------------------------------------------------------------------------
# build_contract_system_prompt
# ---------------------------------------------------------------------------
class TestBuildContractSystemPrompt:
    def test_includes_mode_value(self):
        result = build_contract_system_prompt("explain")
        assert result.endswith("Mode: explain.")

    def test_includes_grounding_instructions(self):
        result = build_contract_system_prompt("chat")
        assert "Vibe Teacher" in result
        assert "Unknown (not in provided code context)" in result
        assert "selected node, file path" in result


# ---------------------------------------------------------------------------
# build_explain_user_prompt
# ---------------------------------------------------------------------------
class TestBuildExplainUserPrompt:
    def test_includes_all_required_json_keys(self):
        result = build_explain_user_prompt(
            code_snippet="def f(): pass",
            level_tone="beginner",
            context="",
            references=_refs(),
        )
        assert "analogy, technical, key_takeaway, sections, unknowns" in result

    def test_includes_all_chat_section_names(self):
        result = build_explain_user_prompt(
            code_snippet="def f(): pass",
            level_tone="beginner",
            context="",
            references=_refs(),
        )
        for section in CHAT_SECTION_ORDER:
            assert section in result

    def test_omits_context_line_when_context_is_empty(self):
        result = build_explain_user_prompt(
            code_snippet="x = 1",
            level_tone="expert",
            context="",
            references=_refs(),
        )
        assert "Context:" not in result

    def test_includes_context_line_when_context_is_present(self):
        result = build_explain_user_prompt(
            code_snippet="x = 1",
            level_tone="expert",
            context="module foo",
            references=_refs(),
        )
        assert "Context: module foo\n" in result

    def test_includes_rendered_references_and_code_block(self):
        result = build_explain_user_prompt(
            code_snippet="x = 1",
            level_tone="expert",
            context="",
            references=_refs(node_id="mod.fn", file_path="mod.py"),
        )
        assert "Selected node: mod.fn" in result
        assert "File path: mod.py" in result
        assert "```python\nx = 1\n```" in result


# ---------------------------------------------------------------------------
# build_chat_user_prompt
# ---------------------------------------------------------------------------
class TestBuildChatUserPrompt:
    def test_includes_all_chat_section_names(self):
        result = build_chat_user_prompt(
            code_snippet="x = 1",
            question="what is x?",
            project_context="",
            references=_refs(),
        )
        for section in CHAT_SECTION_ORDER:
            assert section in result

    def test_includes_question_and_code(self):
        result = build_chat_user_prompt(
            code_snippet="x = 1",
            question="what is x?",
            project_context="",
            references=_refs(),
        )
        assert "User question: what is x?" in result
        assert "```python\nx = 1\n```" in result

    def test_omits_project_context_line_when_empty(self):
        result = build_chat_user_prompt(
            code_snippet="x = 1",
            question="q",
            project_context="",
            references=_refs(),
        )
        assert "Project Context:" not in result

    def test_includes_project_context_line_when_present(self):
        result = build_chat_user_prompt(
            code_snippet="x = 1",
            question="q",
            project_context="a data pipeline",
            references=_refs(),
        )
        assert "Project Context: a data pipeline\n" in result


# ---------------------------------------------------------------------------
# build_ghost_user_prompt
# ---------------------------------------------------------------------------
class TestBuildGhostUserPrompt:
    def test_includes_required_json_keys_and_importance_enum(self):
        result = build_ghost_user_prompt(
            transition="A -> B",
            edge_context="",
            code_snippet="x = 1",
            references=_refs(),
        )
        assert '"narration", "relationship", "importance"' in result
        assert '"high", "medium", "low"' in result

    def test_omits_edge_context_line_when_empty(self):
        result = build_ghost_user_prompt(
            transition="A -> B",
            edge_context="",
            code_snippet="x = 1",
            references=_refs(),
        )
        assert "Edge context:" not in result

    def test_includes_edge_context_line_when_present(self):
        result = build_ghost_user_prompt(
            transition="A -> B",
            edge_context="calls B on success",
            code_snippet="x = 1",
            references=_refs(),
        )
        assert "Edge context: calls B on success\n" in result

    def test_includes_transition_and_code(self):
        result = build_ghost_user_prompt(
            transition="A -> B",
            edge_context="",
            code_snippet="x = 1",
            references=_refs(),
        )
        assert "A -> B" in result
        assert "```python\nx = 1\n```" in result


# ---------------------------------------------------------------------------
# build_refine_learning_user_prompt
# ---------------------------------------------------------------------------
class TestBuildRefineLearningUserPrompt:
    def test_includes_allowed_node_ids_as_json(self):
        result = build_refine_learning_user_prompt(
            slim_steps=[{"node_id": "a", "reason": "r"}],
            allowed_node_ids=["a", "b"],
        )
        assert '["a", "b"]' in result

    def test_includes_baseline_steps_as_json(self):
        result = build_refine_learning_user_prompt(
            slim_steps=[{"node_id": "a", "reason": "r"}],
            allowed_node_ids=["a"],
        )
        assert '[{"node_id": "a", "reason": "r"}]' in result

    def test_includes_critical_reorder_only_rule(self):
        result = build_refine_learning_user_prompt(slim_steps=[], allowed_node_ids=[])
        assert "ONLY reorder the provided list of node_ids" in result

    def test_includes_expected_output_format(self):
        result = build_refine_learning_user_prompt(slim_steps=[], allowed_node_ids=[])
        assert '{"steps": [{"node_id": "...", "reason": "..."}]}' in result


# ---------------------------------------------------------------------------
# build_suggest_learning_user_prompt
# ---------------------------------------------------------------------------
class TestBuildSuggestLearningUserPrompt:
    def test_omits_allowed_node_ids_block_when_none(self):
        result = build_suggest_learning_user_prompt(
            nodes_summary="n1, n2",
            edges_summary="n1->n2",
            file_path="foo.py",
            allowed_node_ids=None,
        )
        assert "allowed_node_ids:" not in result

    def test_omits_allowed_node_ids_block_when_empty_list(self):
        result = build_suggest_learning_user_prompt(
            nodes_summary="n1, n2",
            edges_summary="n1->n2",
            file_path="foo.py",
            allowed_node_ids=[],
        )
        assert "allowed_node_ids:" not in result

    def test_includes_allowed_node_ids_block_when_present(self):
        result = build_suggest_learning_user_prompt(
            nodes_summary="n1, n2",
            edges_summary="n1->n2",
            file_path="foo.py",
            allowed_node_ids=["n1", "n2"],
        )
        assert 'allowed_node_ids:\n["n1", "n2"]\n\n' in result

    def test_includes_file_nodes_and_edges(self):
        result = build_suggest_learning_user_prompt(
            nodes_summary="n1, n2",
            edges_summary="n1->n2",
            file_path="foo.py",
            allowed_node_ids=None,
        )
        assert "File: foo.py" in result
        assert "Nodes:\nn1, n2" in result
        assert "Edges:\nn1->n2" in result

    def test_includes_expected_step_schema(self):
        result = build_suggest_learning_user_prompt(
            nodes_summary="",
            edges_summary="",
            file_path="",
            allowed_node_ids=None,
        )
        assert '{"step": int, "node_id": str, "reason": str}' in result
