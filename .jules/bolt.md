## 2024-05-24 - React Flow Unnecessary Re-renders
**Learning:** In React Flow, state arrays like `nodes` and `edges` trigger O(N) full re-renders on every tick during rapid animations (like Ghost Runner) if object references change, even when visual properties haven't.
**Action:** When mapping over `nodes` or `edges` state to update classes/styles, preserve the exact object references for items whose properties haven't changed.

## 2024-06-12 - React.memo() Anti-Pattern on Simulation Tick Prop
**Learning:** Applying `React.memo()` to a component that receives a prop which changes on every single render cycle (like `stepCount` on simulation ticks) is an anti-pattern. It degrades performance slightly by forcing a useless shallow comparison before rendering.
**Action:** Do not use `React.memo()` on components that depend on fast-changing props unless all other props are stable and you are memoizing specific slow children inside.

## 2024-06-12 - O(N*M) File System Checks during AST Analysis
**Learning:** Repeatedly calling `os.path.isfile()` to check if a module is local inside `ast.walk` creates an O(N*M) bottleneck, where N is the number of files and M is the number of imports per file.
**Action:** Pre-compute a `frozenset` of all local python modules using a single directory scan (`os.walk`), and perform O(1) set membership lookups instead of hitting the filesystem for each import.
## 2026-03-22 - Caching AST Node Lookups vs Full AST Objects
**Learning:** Returning large, complex structures like `ast.AST` from `@functools.lru_cache` functions keeps the entire AST tree alive in memory. Additionally, performing `ast.walk` and `source.splitlines()` on every request is extremely expensive for hot paths like snippet extraction. However, when pre-computing a dictionary of `node.name -> bounds`, you must carefully preserve the original `ast.walk` traversal order's "first-match" behavior for duplicate function names (e.g. `__init__`) by only inserting if the key is absent.
**Action:** When extracting data from ASTs in hot paths, cache primitive, immediately usable structures (like a `dict` mapping node names to line numbers and a `list` of source lines) rather than the raw `ast.AST`. This shifts $O(N)$ operations into a one-time setup cost and enables $O(1)$ lookups, significantly reducing CPU overhead and memory footprint, while being extremely careful to maintain expected collision behavior.
