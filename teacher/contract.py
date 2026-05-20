"""Shared teacher contract for prompts and server-side normalization."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


UNKNOWN_SENTINEL = "Unknown (not in provided code context)."
CHAT_SECTION_ORDER = [
    "What it is",
    "Inputs/Outputs",
    "Side effects",
    "Why this node exists",
    "Common bugs",
    "References",
    "Unknowns",
]
SECTION_BUDGETS = {
    "What it is": 280,
    "Inputs/Outputs": 280,
    "Side effects": 220,
    "Why this node exists": 260,
    "Common bugs": 220,
    "References": 260,
    "Unknowns": 220,
}
EXPLAIN_BUDGETS = {
    "analogy": 240,
    "key_takeaway": 180,
}
GHOST_BUDGETS = {
    "narration": 220,
    "relationship": 180,
}
LEARNING_REASON_BUDGET = 220


@dataclass
class TeacherReferences:
    """Grounding references that must appear in prompts and outputs."""

    node_id: str = ""
    file_path: str | None = None
    callers: list[str] = field(default_factory=list)
    callees: list[str] = field(default_factory=list)
    neighbors: list[str] = field(default_factory=list)

    def render(self) -> str:
        node = self.node_id or "unknown_node"
        file_path = self.file_path or UNKNOWN_SENTINEL
        callers = ", ".join(self.callers) if self.callers else UNKNOWN_SENTINEL
        callees = ", ".join(self.callees) if self.callees else UNKNOWN_SENTINEL
        neighbors = ", ".join(self.neighbors) if self.neighbors else UNKNOWN_SENTINEL
        return (
            f"Selected node: {node}\n"
            f"File path: {file_path}\n"
            f"Callers: {callers}\n"
            f"Callees: {callees}\n"
            f"Neighbors: {neighbors}"
        )


def clip_text(value: str, max_chars: int, fallback: str = UNKNOWN_SENTINEL) -> str:
    text = (value or "").strip()
    if not text:
        return fallback
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _coerce_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _extract_sections_from_text(text: str) -> dict[str, str]:
    section_map: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for raw_line in _coerce_text(text).splitlines():
        line = raw_line.strip()
        matched = False
        for section in CHAT_SECTION_ORDER:
            if line.lower().startswith(section.lower()):
                if current:
                    section_map[current] = "\n".join(buffer).strip()
                current = section
                buffer = []
                matched = True
                break
        if not matched and current:
            buffer.append(raw_line)
    if current:
        section_map[current] = "\n".join(buffer).strip()
    return section_map


def _normalize_contract_sections(
    parsed: dict[str, object],
    references: TeacherReferences,
) -> dict[str, str]:
    sections_payload = parsed.get("sections")
    if not isinstance(sections_payload, dict):
        sections_payload = {}
    unknowns_payload = parsed.get("unknowns")
    unknowns_list: list[str] = []
    if isinstance(unknowns_payload, list):
        unknowns_list = [_coerce_text(item).strip() for item in unknowns_payload]
    section_map = {
        section: clip_text(
            _coerce_text(sections_payload.get(section, "")),
            SECTION_BUDGETS[section],
        )
        for section in CHAT_SECTION_ORDER
    }
    references_text = clip_text(
        _coerce_text(sections_payload.get("References", references.render())),
        SECTION_BUDGETS["References"],
        fallback=references.render(),
    )
    section_map["References"] = references_text
    if unknowns_list:
        unknown_block = ", ".join(item for item in unknowns_list if item)
    else:
        unknown_block = _coerce_text(sections_payload.get("Unknowns", ""))
    section_map["Unknowns"] = clip_text(
        unknown_block,
        SECTION_BUDGETS["Unknowns"],
        fallback=UNKNOWN_SENTINEL,
    )
    return section_map


def render_contract_text(section_map: dict[str, str]) -> str:
    blocks: list[str] = []
    for section in CHAT_SECTION_ORDER:
        body = clip_text(section_map.get(section, ""), SECTION_BUDGETS[section])
        blocks.append(f"### {section}\n{body}")
    return "\n\n".join(blocks)


def normalize_chat_text(raw_text: str, references: TeacherReferences) -> str:
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            sections = _normalize_contract_sections(parsed, references)
            return render_contract_text(sections)
    except json.JSONDecodeError:
        pass

    extracted = _extract_sections_from_text(raw_text)
    if not extracted:
        extracted["What it is"] = clip_text(raw_text, SECTION_BUDGETS["What it is"])
    extracted["References"] = references.render()
    extracted["Unknowns"] = UNKNOWN_SENTINEL
    normalized = {
        section: clip_text(extracted.get(section, ""), SECTION_BUDGETS[section])
        for section in CHAT_SECTION_ORDER
    }
    return render_contract_text(normalized)


def normalize_explain_payload(
    parsed: dict[str, object],
    references: TeacherReferences,
) -> dict[str, str]:
    analogy = clip_text(
        _coerce_text(parsed.get("analogy", "")), EXPLAIN_BUDGETS["analogy"]
    )
    takeaway = clip_text(
        _coerce_text(parsed.get("key_takeaway", "")),
        EXPLAIN_BUDGETS["key_takeaway"],
    )
    sections = _normalize_contract_sections(parsed, references)
    technical = render_contract_text(sections)
    return {
        "analogy": analogy,
        "technical": technical,
        "key_takeaway": takeaway,
    }


def normalize_ghost_payload(
    parsed: dict[str, object],
    references: TeacherReferences,
) -> dict[str, str]:
    importance = _coerce_text(parsed.get("importance", "medium")).strip().lower()
    if importance not in {"high", "medium", "low"}:
        importance = "medium"
    narration = clip_text(
        _coerce_text(parsed.get("narration", "")),
        GHOST_BUDGETS["narration"],
    )
    relationship = clip_text(
        _coerce_text(parsed.get("relationship", references.render())),
        GHOST_BUDGETS["relationship"],
        fallback=references.render(),
    )
    return {
        "narration": narration,
        "relationship": relationship,
        "importance": importance,
    }


def normalize_learning_steps(
    steps: object,
    *,
    allowed_node_ids: list[str] | None,
    include_step_numbers: bool,
) -> list[dict[str, object]]:
    if not isinstance(steps, list):
        return []
    allowed = set(allowed_node_ids or [])
    normalized: list[dict[str, object]] = []
    used: set[str] = set()
    for idx, item in enumerate(steps, start=1):
        if not isinstance(item, dict):
            continue
        node_id = _coerce_text(item.get("node_id")).strip()
        if not node_id:
            continue
        if allowed and node_id not in allowed:
            continue
        if node_id in used:
            continue
        reason = clip_text(_coerce_text(item.get("reason", "")), LEARNING_REASON_BUDGET)
        entry: dict[str, object] = {"node_id": node_id, "reason": reason}
        if include_step_numbers:
            step_value = item.get("step")
            step = step_value if isinstance(step_value, int) and step_value > 0 else idx
            entry["step"] = step
        normalized.append(entry)
        used.add(node_id)
    if include_step_numbers:
        return [{**item, "step": i} for i, item in enumerate(normalized, start=1)]
    return normalized


def build_contract_system_prompt(mode: str) -> str:
    return (
        "You are 'Vibe Teacher', a grounded code tutor. "
        "Only use facts from provided code and metadata. "
        "If evidence is missing, state Unknown (not in provided code context).\n"
        "Always reference selected node, file path, and known callers/callees/neighbors.\n"
        f"Mode: {mode}."
    )


def build_explain_user_prompt(
    *,
    code_snippet: str,
    level_tone: str,
    context: str,
    references: TeacherReferences,
) -> str:
    context_line = f"Context: {context}\n" if context else ""
    return (
        "Return JSON with keys: analogy, technical, key_takeaway, sections, unknowns.\n"
        "sections must include exactly: " + ", ".join(CHAT_SECTION_ORDER) + ".\n"
        "unknowns must list missing facts.\n"
        f"Target Audience: {level_tone}\n"
        f"{context_line}"
        f"References:\n{references.render()}\n\n"
        f"Code:\n```python\n{code_snippet}\n```"
    )


def build_chat_user_prompt(
    *,
    code_snippet: str,
    question: str,
    project_context: str,
    references: TeacherReferences,
) -> str:
    context_line = f"Project Context: {project_context}\n" if project_context else ""
    return (
        "Answer using JSON with keys: sections and unknowns.\n"
        "sections must contain these exact keys: "
        + ", ".join(CHAT_SECTION_ORDER)
        + ".\n"
        "Keep each section concise and grounded.\n"
        f"{context_line}"
        f"References:\n{references.render()}\n\n"
        f"Code:\n```python\n{code_snippet}\n```\n\n"
        f"User question: {question}"
    )


def build_ghost_user_prompt(
    *,
    transition: str,
    edge_context: str,
    code_snippet: str,
    references: TeacherReferences,
) -> str:
    edge = f"Edge context: {edge_context}\n" if edge_context else ""
    return (
        'Return ONLY JSON with keys "narration", "relationship", "importance".\n'
        'importance must be one of: "high", "medium", "low".\n'
        "If relation is unknown, say Unknown (not in provided code context).\n"
        f"References:\n{references.render()}\n\n"
        f"{transition}\n"
        f"{edge}"
        f"Code:\n```python\n{code_snippet}\n```"
    )


def build_refine_learning_user_prompt(
    *,
    slim_steps: list[dict[str, object]],
    allowed_node_ids: list[str],
) -> str:
    return (
        "Rules:\n"
        "- Reorder only the provided node_ids.\n"
        "- Do not add/remove node_ids.\n"
        "- Reasons must be grounded in provided steps/metadata.\n"
        "- If evidence is missing, use Unknown (not in provided code context).\n\n"
        f"allowed_node_ids:\n{json.dumps(allowed_node_ids)}\n\n"
        f"baseline_steps:\n{json.dumps(slim_steps)}\n\n"
        'Return JSON: {"steps": [{"node_id": "...", "reason": "..."}]}'
    )


def build_suggest_learning_user_prompt(
    *,
    nodes_summary: str,
    edges_summary: str,
    file_path: str,
    allowed_node_ids: list[str] | None,
) -> str:
    allowed_line = (
        f"allowed_node_ids:\n{json.dumps(allowed_node_ids)}\n\n"
        if allowed_node_ids
        else ""
    )
    return (
        "Return JSON object with one key: steps.\n"
        'Each step: {"step": int, "node_id": str, "reason": str}.\n'
        "Reasons must stay grounded in provided graph. If unknown, explicitly say so.\n\n"
        f"{allowed_line}"
        f"File: {file_path}\n"
        f"Nodes:\n{nodes_summary}\n\n"
        f"Edges:\n{edges_summary}\n"
    )


def extract_node_ids_from_summary(nodes_summary: str) -> list[str]:
    ids: list[str] = []
    for part in nodes_summary.split(","):
        token = part.strip()
        if not token:
            continue
        match = re.match(r"([^\s(]+)", token)
        if not match:
            continue
        ids.append(match.group(1))
    return ids
