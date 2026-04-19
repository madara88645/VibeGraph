## 2024-05-24 - React Flow Unnecessary Re-renders
**Learning:** In React Flow, state arrays like `nodes` and `edges` trigger O(N) full re-renders on every tick during rapid animations (like Ghost Runner) if object references change, even when visual properties haven't.     
**Action:** When mapping over `nodes` or `edges` state to update classes/styles, preserve the exact object references for items whose properties haven't changed.

## 2024-06-12 - React.memo() Anti-Pattern on Simulation Tick Prop
**Learning:** Applying `React.memo()` to a component that receives a prop which changes on every single render cycle (like `stepCount` on simulation ticks) is an anti-pattern. It degrades performance slightly by forcing a useless shallow comparison before rendering.
**Action:** Do not use `React.memo()` on components that depend on fast-changing props unless all other props are stable and you are memoizing specific slow children inside.

## 2024-06-12 - O(N*M) File System Checks during AST Analysis
**Learning:** Repeatedly calling `os.path.isfile()` to check if a module is local inside `ast.walk` creates an O(N*M) bottleneck, where N is the number of files and M is the number of imports per file.
**Action:** Pre-compute a `frozenset` of all local python modules using a single directory scan (`os.walk`), and perform O(1) set membership lookups instead of hitting the filesystem for each import.

## 2024-11-20 - O(N log N) Array Sorts in High-Frequency Execution Paths
**Learning:** In React hooks like `useGhostRunner`, using `[...array].filter().sort().find()` inside high-frequency interval ticks introduces significant overhead due to object cloning and O(N log N) sorting just to find a single maximum element.
**Action:** Replace `O(N log N)` array sorts with `O(N)` single-pass linear loops that track tracking variables when searching for a single element (e.g., node with the highest degree). Explicitly track default states (like `> -1` for non-negative graph degrees) to cleanly preserve original fallback and error behaviors.

## 2026-04-13 - Array slice over-fetching overhead
**Learning:** In React components that perform fuzzy search filtering over large datasets (like  evaluating thousands of nodes), using  creates a massive hidden O(N) performance bottleneck because it evaluates the condition against the entire array before discarding all but the first K results.
**Action:** Replace  chains with standard  loops and an early  condition when the required number of top-K results is reached. This drops the execution time from an unconditional O(N) down to a best-case O(K).

## 2025-02-20 - Array slice over-fetching overhead
**Learning:** In React components that perform fuzzy search filtering over large datasets (like `SearchBar.jsx` evaluating thousands of nodes), using `array.filter(condition).slice(0, K)` creates a massive hidden O(N) performance bottleneck because it evaluates the condition against the entire array before discarding all but the first K results.
**Action:** Replace `.filter().slice()` chains with standard `for` loops and an early `break` condition when the required number of top-K results is reached. This drops the execution time from an unconditional O(N) down to a best-case O(K).

## 2025-02-20 - O(N) Array Iteration Chain Bottleneck
**Learning:** In React hooks, calculating complex derived state by chaining multiple `array.filter()`, `array.map()`, and `array.forEach()` operations creates hidden performance bottlenecks by generating intermediate arrays and triggering multiple O(N) passes.
**Action:** Replace multiple O(N) array method chains with a single iterative `for` loop that accumulates all required metrics in a single O(N) pass, significantly reducing CPU overhead and memory allocations.

## 2024-05-13 - Array map over-fetching overhead
**Learning:** In React components that evaluate data arrays to build summary lists, combining `.filter(condition).slice(0, K).map()` introduces an unconditional O(N) performance bottleneck because `.filter()` processes the entire array before `.slice()` applies the limit.
**Action:** Replace `.filter().slice().map()` chains with standard `for` loops and an early `break` condition when the desired K count is reached. This drops the execution time to a best-case O(K), drastically improving responsiveness when traversing massive node arrays.

## 2024-05-13 - Array map over-fetching overhead
**Learning:** In React components that evaluate data arrays to build summary lists, combining `.filter(condition).slice(0, K).map()` introduces an unconditional O(N) performance bottleneck because `.filter()` processes the entire array before `.slice()` applies the limit.
**Action:** Replace `.filter().slice().map()` chains with standard `for` loops and an early `break` condition when the desired K count is reached. This drops the execution time to a best-case O(K), drastically improving responsiveness when traversing massive node arrays.

## 2024-05-14 - Redundant Array Traversal and Allocation
**Learning:** Chaining multiple array methods like `.reduce()`, `.map()`, and `.filter()` over large datasets (like `allNodes`) creates hidden O(N) bottlenecks by executing multiple full iterations and allocating temporary intermediate arrays for each step.
**Action:** Consolidate these operations into a single imperative `for` loop to gather all required metrics and collections in one pass, minimizing memory allocations and CPU overhead without changing functionality.
## 2024-05-25 - ReactFlow Re-render Optimization
**Learning:** In React Flow applications, wrapping a heavyweight graph component (like `GraphViewer`) in `memo()` is crucial when the parent component experiences rapid, high-frequency state updates (like a simulation tick), because it prevents O(N) re-renders of the entire graph node/edge structure when the props sent to the graph remain referentially stable.
**Action:** Use `memo()` on ReactFlow wrapper components to isolate them from parent re-renders, explicitly importing `memo` from `'react'`.

## 2025-02-21 - Array Iteration Chain Bottleneck in High-Frequency Hooks
**Learning:** In high-frequency React hooks (e.g., `useGhostRunner.js` simulation ticks), chaining functional array methods like `.filter().map().filter()` over large datasets (like graph edges or nodes) causes severe performance bottlenecks. It creates multiple O(N) passes over the data and allocates several intermediate arrays on every single animation frame or interval tick.
**Action:** Replace multiple O(N) functional array method chains with a single imperative `for` loop that accumulates all required metrics in a single O(N) pass. This drastically reduces CPU overhead and intermediate object allocations.
