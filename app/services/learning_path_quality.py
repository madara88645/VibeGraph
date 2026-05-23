"""Quality checks and repair for repo-wide learning paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.learning_path import normalize_graph


@dataclass
class QualityReport:
    caller_before_callee: bool
    complete_and_unique: bool
    step_numbers_valid: bool
    violating_edges: list[tuple[str, str]] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            self.caller_before_callee
            and self.complete_and_unique
            and self.step_numbers_valid
        )


def _call_edges(outgoing: dict[str, list[str]]) -> list[tuple[str, str]]:
    return [(source, target) for source, targets in outgoing.items() for target in targets]


def _ordered_node_ids(steps: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for step in steps:
        node_id = step.get("node_id")
        if isinstance(node_id, str) and node_id:
            ids.append(node_id)
    return ids


def assess_learning_path(
    steps: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> QualityReport:
    normalized_nodes, outgoing, _ = normalize_graph(nodes, edges)
    expected_ids = set(normalized_nodes)
    ordered_ids = _ordered_node_ids(steps)
    positions = {node_id: index for index, node_id in enumerate(ordered_ids)}

    violating_edges: list[tuple[str, str]] = []
    for caller, callee in _call_edges(outgoing):
        caller_pos = positions.get(caller)
        callee_pos = positions.get(callee)
        if caller_pos is None or callee_pos is None:
            continue
        if caller_pos >= callee_pos:
            violating_edges.append((caller, callee))

    caller_before_callee = not violating_edges

    seen: set[str] = set()
    duplicates: list[str] = []
    for node_id in ordered_ids:
        if node_id in seen:
            duplicates.append(node_id)
        seen.add(node_id)

    complete_and_unique = (
        len(ordered_ids) == len(expected_ids)
        and seen == expected_ids
        and not duplicates
    )

    expected_steps = list(range(1, len(steps) + 1))
    actual_steps = [step.get("step") for step in steps]
    step_numbers_valid = actual_steps == expected_steps

    violations: list[str] = []
    if not caller_before_callee:
        for caller, callee in violating_edges:
            violations.append(
                f"caller_before_callee: {caller} must appear before {callee}"
            )
    if duplicates:
        violations.append(f"complete_and_unique: duplicate node_ids {duplicates}")
    if seen != expected_ids:
        missing = sorted(expected_ids - seen)
        extra = sorted(seen - expected_ids)
        if missing:
            violations.append(f"complete_and_unique: missing node_ids {missing}")
        if extra:
            violations.append(f"complete_and_unique: unknown node_ids {extra}")
    if not step_numbers_valid:
        violations.append(
            f"step_numbers_valid: expected {expected_steps}, got {actual_steps}"
        )

    return QualityReport(
        caller_before_callee=caller_before_callee,
        complete_and_unique=complete_and_unique,
        step_numbers_valid=step_numbers_valid,
        violating_edges=violating_edges,
        violations=violations,
    )


def repair_caller_before_callee(
    ordered_ids: list[str],
    outgoing: dict[str, list[str]],
) -> list[str]:
    """Move callers before callees when leftover or AI ordering violates Q1."""
    order = list(ordered_ids)
    edges = _call_edges(outgoing)
    if not edges:
        return order

    limit = len(order) ** 2 + 1
    for _ in range(limit):
        positions = {node_id: index for index, node_id in enumerate(order)}
        violation: tuple[str, str] | None = None
        for caller, callee in edges:
            caller_pos = positions.get(caller)
            callee_pos = positions.get(callee)
            if caller_pos is None or callee_pos is None:
                continue
            if caller_pos > callee_pos:
                violation = (caller, callee)
                break
        if violation is None:
            break
        caller, callee = violation
        order.remove(caller)
        order.insert(order.index(callee), caller)
    return order


def apply_learning_path_quality(
    steps: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not steps:
        return steps

    report = assess_learning_path(steps, nodes, edges)
    if report.caller_before_callee:
        return steps

    _, outgoing, _ = normalize_graph(nodes, edges)
    by_id = {step["node_id"]: step for step in steps if isinstance(step.get("node_id"), str)}
    repaired_ids = repair_caller_before_callee(_ordered_node_ids(steps), outgoing)
    return [
        {**by_id[node_id], "step": index}
        for index, node_id in enumerate(repaired_ids, start=1)
        if node_id in by_id
    ]
