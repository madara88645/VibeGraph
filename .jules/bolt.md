## 2024-05-24 - React Flow Unnecessary Re-renders
**Learning:** In React Flow, state arrays like `nodes` and `edges` trigger O(N) full re-renders on every tick during rapid animations (like Ghost Runner) if object references change, even when visual properties haven't.
**Action:** When mapping over `nodes` or `edges` state to update classes/styles, preserve the exact object references for items whose properties haven't changed.

## 2024-06-12 - React.memo() Anti-Pattern on Simulation Tick Prop
**Learning:** Applying `React.memo()` to a component that receives a prop which changes on every single render cycle (like `stepCount` on simulation ticks) is an anti-pattern. It degrades performance slightly by forcing a useless shallow comparison before rendering.
**Action:** Do not use `React.memo()` on components that depend on fast-changing props unless all other props are stable and you are memoizing specific slow children inside.

## 2024-06-12 - O(N*M) File System Checks during AST Analysis
**Learning:** Repeatedly calling `os.path.isfile()` to check if a module is local inside `ast.walk` creates an O(N*M) bottleneck, where N is the number of files and M is the number of imports per file.
**Action:** Pre-compute a `frozenset` of all local python modules using a single directory scan (`os.walk`), and perform O(1) set membership lookups instead of hitting the filesystem for each import.
## 2024-06-25 - NetworkX Simple Cycles O((V+E)C) Exponential Blowup
**Learning:** `nx.simple_cycles` is an NP-hard operation ($O((V+E)C)$) and scales exponentially with the number of cycles ($C$). Using it in production to merely check if an edge is part of *any* cycle will cause severe CPU hangs/timeouts on densely connected graphs.
**Action:** When you only need to determine cycle participation (not enumerate every unique cycle path), use Tarjan's `nx.strongly_connected_components`. It runs in pure linear $O(V+E)$ time. An edge is part of a cycle if both its `u` and `v` nodes exist in the same strongly connected component of size > 1.
