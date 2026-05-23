# Learning path quality rubric

VibeGraph builds study order from the **call graph**: each edge means `source` calls `target`. The learning path is **top-down** (execution-following): you meet callers before the functions they call, starting from entry points. This is **not** academic prerequisite order (learn callee before caller).

Implementation: [`app/services/learning_path.py`](../app/services/learning_path.py) (generation) and [`app/services/learning_path_quality.py`](../app/services/learning_path_quality.py) (checks and repair).

## How generation relates to the graph

1. Score nodes (entry point, public API, hubs, complexity).
2. Priority heap walk from **all** entry points along **outgoing** call edges.
3. Append unvisited nodes in score-sorted buckets (public/hubs, then internals).
4. Optionally AI-refine the first 8 steps (reasons and light reorder).
5. **Repair** if any call edge would place a caller after its callee.

Sibling callees may reorder by score (e.g. two functions both called from `main`) — that is intentional and not a rubric failure.

## Known violation sources (before repair)

| Source | What goes wrong |
|--------|------------------|
| Leftover bucket | Unreachable callers appended after a callee they call |
| AI refine window | Model permutes steps without edge context in the prompt |

Server-side repair moves callers to just before their callees when Q1 fails.

## Measurable checks

| ID | Name | Pass criterion |
|----|------|----------------|
| **Q1** | `caller_before_callee` | For every call edge `(u, v)`, `index(u) < index(v)` in the path |
| **Q2** | `complete_and_unique` | Every graph node appears exactly once; `len(steps) == len(nodes)` |
| **Q3** | `step_numbers_valid` | `step` values are `1..N` with no gaps |

`assess_learning_path()` returns a report with booleans and human-readable `violations`. Q1 also lists `violating_edges` as `(caller, callee)` pairs.

## API usage

After `build_learning_path(nodes, edges)` or `refine_learning_path_with_ai(..., nodes=..., edges=...)`, quality enforcement runs automatically. To inspect without changing order, call `assess_learning_path(steps, nodes, edges)` directly in tests or tooling.
