"""Deterministic repo-wide learning path generation."""

from __future__ import annotations

import heapq
import os
from collections import defaultdict
from typing import Any, Callable


AI_REFINEMENT_WINDOW = 8


def _node_data(raw_node: dict[str, Any]) -> dict[str, Any]:
    data = raw_node.get("data")
    return data if isinstance(data, dict) else {}


def _basename(path: str | None) -> str:
    if not path:
        return ""
    return os.path.basename(path.replace("\\", "/"))


def _is_public_api(node_id: str, data: dict[str, Any]) -> bool:
    if isinstance(data.get("public_api"), bool):
        return data["public_api"]
    label = str(data.get("label") or node_id)
    name = label.rsplit(".", 1)[-1]
    return not name.startswith("_")


def _is_entry_point(node_id: str, data: dict[str, Any]) -> bool:
    if data.get("entry_point") is True:
        return True
    label = str(data.get("label") or node_id)
    name = label.rsplit(".", 1)[-1]
    file_name = _basename(data.get("file"))
    return name in {"main", "run", "app"} or file_name in {
        "__main__.py",
        "cli.py",
        "main.py",
        "serve.py",
    }


def _complexity_penalty(data: dict[str, Any]) -> float:
    loc = max(int(data.get("loc") or 0), 0)
    nesting = max(int(data.get("nesting_depth") or 0), 0)
    deps = max(int(data.get("dependency_count") or 0), 0)
    return min(30.0, loc / 8.0 + nesting * 3.0 + deps * 1.5)


def _reason(signals: dict[str, Any]) -> str:
    reasons: list[str] = []
    if signals["entry_point"]:
        reasons.append("Start here because it is a real entry point.")
    if signals["api_boundary"]:
        reasons.append("It exposes a public API boundary.")
    elif signals["public_api"]:
        reasons.append("It is public-facing code rather than an internal helper.")
    if signals["hub_score"] >= 20:
        reasons.append("It is a call-graph hub.")
    if signals["side_effect_boundary"]:
        reasons.append("It touches side effects like I/O, network, or framework edges.")
    if not reasons:
        reasons.append("Read this after the higher-level flow is clear.")
    return " ".join(reasons)


def _normalize_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], dict[str, int]]:
    normalized_nodes: dict[str, dict[str, Any]] = {}
    for raw_node in nodes:
        node_id = raw_node.get("id")
        if not isinstance(node_id, str) or not node_id:
            continue
        normalized_nodes[node_id] = _node_data(raw_node)

    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming_count = {node_id: 0 for node_id in normalized_nodes}
    seen_edges: set[tuple[str, str]] = set()
    for raw_edge in edges:
        source = raw_edge.get("source")
        target = raw_edge.get("target")
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in normalized_nodes
            or target not in normalized_nodes
        ):
            continue
        edge = (source, target)
        if edge in seen_edges:
            continue
        seen_edges.add(edge)
        outgoing[source].append(target)
        incoming_count[target] += 1

    for targets in outgoing.values():
        targets.sort()

    return normalized_nodes, outgoing, incoming_count


def build_learning_path(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    normalized_nodes, outgoing, incoming_count = _normalize_graph(nodes, edges)
    if not normalized_nodes:
        return []

    max_fan_out = max(
        (len(outgoing[node_id]) for node_id in normalized_nodes), default=0
    )
    max_fan_in = max(incoming_count.values(), default=0)
    scored: dict[str, dict[str, Any]] = {}

    for node_id, data in normalized_nodes.items():
        fan_out = len(outgoing[node_id])
        fan_in = incoming_count[node_id]
        fan_out_score = (fan_out / max_fan_out * 25.0) if max_fan_out else 0.0
        fan_in_score = (fan_in / max_fan_in * 25.0) if max_fan_in else 0.0
        hub_score = fan_out_score + fan_in_score
        entry_point = _is_entry_point(node_id, data)
        public_api = _is_public_api(node_id, data)
        api_boundary = bool(data.get("api_boundary"))
        side_effect_boundary = bool(data.get("side_effect_boundary"))
        score = (
            (100.0 if entry_point else 0.0)
            + (30.0 if public_api else 0.0)
            + (25.0 if api_boundary else 0.0)
            + (25.0 if side_effect_boundary else 0.0)
            + hub_score
            - _complexity_penalty(data)
        )
        signals = {
            "entry_point": entry_point,
            "public_api": public_api,
            "api_boundary": api_boundary,
            "side_effect_boundary": side_effect_boundary,
            "fan_in": fan_in,
            "fan_out": fan_out,
            "hub_score": round(hub_score, 2),
        }
        scored[node_id] = {
            "node_id": node_id,
            "node_name": data.get("label") or node_id,
            "file_path": data.get("file"),
            "score": round(score, 2),
            "signals": signals,
            "reason": _reason(signals),
            "_sort": (
                0 if entry_point else 1,
                -(round(score, 4)),
                str(data.get("file") or ""),
                int(data.get("lineno") or 0),
                node_id,
            ),
        }

    entries = [
        node_id for node_id, step in scored.items() if step["signals"]["entry_point"]
    ]
    start_nodes = entries or list(scored)
    start = sorted(start_nodes, key=lambda node_id: scored[node_id]["_sort"])[0]

    ordered_ids: list[str] = []
    visited: set[str] = set()
    queue: list[tuple[tuple[Any, ...], str]] = []

    def push(node_id: str) -> None:
        if node_id not in visited:
            heapq.heappush(queue, (scored[node_id]["_sort"], node_id))

    push(start)
    while queue:
        _, node_id = heapq.heappop(queue)
        if node_id in visited:
            continue
        visited.add(node_id)
        ordered_ids.append(node_id)
        for target in outgoing[node_id]:
            push(target)

    remaining_public_hubs = [
        node_id
        for node_id in scored
        if node_id not in visited
        and (
            scored[node_id]["signals"]["public_api"]
            or scored[node_id]["signals"]["hub_score"] > 0
        )
    ]
    remaining_internals = [
        node_id
        for node_id in scored
        if node_id not in visited and node_id not in remaining_public_hubs
    ]

    for node_id in sorted(
        remaining_public_hubs, key=lambda item: scored[item]["_sort"]
    ):
        visited.add(node_id)
        ordered_ids.append(node_id)
    for node_id in sorted(remaining_internals, key=lambda item: scored[item]["_sort"]):
        ordered_ids.append(node_id)

    steps = []
    for index, node_id in enumerate(ordered_ids, start=1):
        step = {key: value for key, value in scored[node_id].items() if key != "_sort"}
        step["step"] = index
        steps.append(step)
    return steps


def refine_learning_path_with_ai(
    baseline_steps: list[dict[str, Any]],
    refiner: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    window_size: int = AI_REFINEMENT_WINDOW,
) -> list[dict[str, Any]]:
    if not baseline_steps:
        return []

    window = baseline_steps[:window_size]
    window_ids = {step["node_id"] for step in window}
    try:
        proposed = refiner(window)
    except Exception:
        proposed = []

    used: set[str] = set()
    merged_window: list[dict[str, Any]] = []
    by_id = {step["node_id"]: step for step in window}
    for item in proposed or []:
        if not isinstance(item, dict):
            continue
        node_id = item.get("node_id")
        if not isinstance(node_id, str) or node_id not in window_ids or node_id in used:
            continue
        next_step = {**by_id[node_id]}
        reason = item.get("reason")
        if isinstance(reason, str) and reason.strip():
            next_step["reason"] = reason.strip()
        merged_window.append(next_step)
        used.add(node_id)

    for step in window:
        if step["node_id"] not in used:
            merged_window.append(step)

    merged = merged_window + baseline_steps[window_size:]
    return [{**step, "step": index} for index, step in enumerate(merged, start=1)]
