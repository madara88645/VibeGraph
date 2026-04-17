## 2024-05-24 - React Flow Unnecessary Re-renders
**Learning:** In React Flow, state arrays like `nodes` and `edges` trigger O(N) full re-renders on every tick during rapid animations (like Ghost Runner) if object references change, even when visual properties haven't.
**Action:** When mapping over `nodes` or `edges` state to update classes/styles, preserve the exact object references for items whose properties haven't changed.

## 2024-06-12 - React.memo() Anti-Pattern on Simulation Tick Prop
**Learning:** Applying `React.memo()` to a component that receives a prop which changes on every single render cycle (like `stepCount` on simulation ticks) is an anti-pattern. It degrades performance slightly by forcing a useless shallow comparison before rendering.
**Action:** Do not use `React.memo()` on components that depend on fast-changing props unless all other props are stable and you are memoizing specific slow children inside.

## 2024-06-12 - O(N*M) File System Checks during AST Analysis
**Learning:** Repeatedly calling `os.path.isfile()` to check if a module is local inside `ast.walk` creates an O(N*M) bottleneck, where N is the number of files and M is the number of imports per file.
**Action:** Pre-compute a `frozenset` of all local python modules using a single directory scan (`os.walk`), and perform O(1) set membership lookups instead of hitting the filesystem for each import.## 2024-11-20 - O(N log N) Array Sorts in High-Frequency Execution Paths
**Learning:** In React hooks like `useGhostRunner`, using `[...array].filter().sort().find()` inside high-frequency interval ticks introduces significant overhead due to object cloning and O(N log N) sorting just to find a single maximum element.
**Action:** Replace `O(N log N)` array sorts with `O(N)` single-pass linear loops that track tracking variables when searching for a single element (e.g., node with the highest degree). Explicitly track default states (like `> -1` for non-negative graph degrees) to cleanly preserve original fallback and error behaviors.

## 2026-04-13 - Array slice over-fetching overhead
**Learning:** In React components that perform fuzzy search filtering over large datasets (like  evaluating thousands of nodes), using  creates a massive hidden O(N) performance bottleneck because it evaluates the condition against the entire array before discarding all but the first K results.
**Action:** Replace  chains with standard  loops and an early  condition when the required number of top-K results is reached. This drops the execution time from an unconditional O(N) down to a best-case O(K).

## 2025-02-20 - Array slice over-fetching overhead
**Learning:** In React components that perform fuzzy search filtering over large datasets (like `SearchBar.jsx` evaluating thousands of nodes), using `array.filter(condition).slice(0, K)` creates a massive hidden O(N) performance bottleneck because it evaluates the condition against the entire array before discarding all but the first K results.
**Action:** Replace `.filter().slice()` chains with standard `for` loops and an early `break` condition when the required number of top-K results is reached. This drops the execution time from an unconditional O(N) down to a best-case O(K).

## 2024-05-18 - Optimize Path Traversal Check in Security Utilities
**Learning:** When checking for specific string elements (like `".."` for path traversal) in a list of path segments, using the native `in` operator (e.g., `".." in parts`) is significantly faster than using a generator expression with `any()` (e.g., `any(part == ".." for part in parts)`). The `in` operator leverages Python's highly optimized C-level iteration and equality checks, bypassing the overhead of creating and advancing a Python generator.
**Action:** Replaced `any(part == ".." for part in parts)` with `".." in parts` in `app/utils/security.py`, resulting in an ~88% speedup for this specific check during file path normalization.
