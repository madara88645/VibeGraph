## 2024-05-24 - React Flow Unnecessary Re-renders
**Learning:** In React Flow, state arrays like `nodes` and `edges` trigger O(N) full re-renders on every tick during rapid animations (like Ghost Runner) if object references change, even when visual properties haven't.
**Action:** When mapping over `nodes` or `edges` state to update classes/styles, preserve the exact object references for items whose properties haven't changed.

## 2024-06-12 - React.memo() Anti-Pattern on Simulation Tick Prop
**Learning:** Applying `React.memo()` to a component that receives a prop which changes on every single render cycle (like `stepCount` on simulation ticks) is an anti-pattern. It degrades performance slightly by forcing a useless shallow comparison before rendering.
**Action:** Do not use `React.memo()` on components that depend on fast-changing props unless all other props are stable and you are memoizing specific slow children inside.

## 2024-06-12 - O(N*M) File System Checks during AST Analysis
**Learning:** Repeatedly calling `os.path.isfile()` to check if a module is local inside `ast.walk` creates an O(N*M) bottleneck, where N is the number of files and M is the number of imports per file.
**Action:** Pre-compute a `frozenset` of all local python modules using a single directory scan (`os.walk`), and perform O(1) set membership lookups instead of hitting the filesystem for each import.
## 2024-06-25 - Redundant os.makedirs Syscalls during Extraction
**Learning:** During ZIP archive extraction, calling `os.makedirs(..., exist_ok=True)` for every single file causes a severe I/O bottleneck due to redundant filesystem checks when thousands of files map to the same directory.
**Action:** Use a `set()` to cache the paths of directories that have already been created within the extraction loop, and only call `os.makedirs` if the path is not in the cache.

## 2024-06-25 - Unsafe React useMemo String Heuristics
**Learning:** Attempting to optimize `useMemo` array dependencies by substituting arrays with string heuristics (like `${array.length}-${array[0].id}`) is unsafe. It breaks React's reactivity by failing to detect when internal properties or later elements change, leading to silent stale state bugs.
**Action:** Always avoid string-based array substitution heuristics. If an array reference changes rapidly but its relevant data doesn't, encode the exact fields that affect the logic into a stable string key, or reconsider the architecture instead of creating a brittle heuristic.
