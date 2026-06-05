> **Read first:** [instructions.md](./instructions.md). Past learnings only — do not apply repo-wide without a task-specific reason.

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

## 2024-05-18 - Optimize Path Traversal Check in Security Utilities
**Learning:** When checking for specific string elements (like `".."` for path traversal) in a list of path segments, using the native `in` operator (e.g., `".." in parts`) is significantly faster than using a generator expression with `any()` (e.g., `any(part == ".." for part in parts)`). The `in` operator leverages Python's highly optimized C-level iteration and equality checks, bypassing the overhead of creating and advancing a Python generator.
**Action:** Replaced `any(part == ".." for part in parts)` with `".." in parts` in `app/utils/security.py`, resulting in an ~88% speedup for this specific check during file path normalization.

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

## 2024-05-18 - Optimize array searches by extracting fallback subsets
**Learning:** When optimizing sequential fallback searches over large arrays in high-frequency React hooks (e.g., searching for a specific node and falling back to another in `useGhostRunner.js`), consolidate multiple `O(N)` `.find()` calls into a single `O(N)` `for` loop, or cache subsets to avoid iterating the whole array.
**Action:** Created `entryPointsRef` populated on mount/node-change to reduce a large O(N) array scan for `entry_point` nodes down to scanning a pre-filtered list, achieving ~500x speedup in the worst case.
## 2026-05-23 - Zero-allocation primitives for useMemo
**Learning:** In high-frequency React hooks (e.g., simulation ticks), creating complex string-based keys (like `array.map().join()`) or using `.split().filter()` to derive primitive counts for memoization is a severe anti-pattern that creates massive garbage collection pressure.
**Action:** Compute these primitive values directly using a fast, zero-allocation imperative `for` loop inside the `useMemo` block. Because `useMemo` returns a primitive, downstream components still correctly bail out of renders if the value doesn't change, while eliminating the allocation overhead entirely.

## 2024-06-25 - Python AST Traversal Optimization
**Learning:** Using `ast.walk(tree)` to find specific block-level declarations (like FunctionDef or ClassDef) is incredibly slow for large files because it recursively visits every single leaf node in the AST (names, constants, operators).
**Action:** Replace `ast.walk()` with a custom Breadth-First Search (BFS) using `collections.deque` that strictly checks the current node type, and only appends children from structural block attributes (`body`, `orelse`, `handlers`, `finalbody`, `cases`) to the queue. This safely skips thousands of leaf nodes while preserving the exact BFS traversal order needed for correct name-shadowing behavior.

## 2024-04-28 - Zero-allocation string processing in high-frequency React renders
**Learning:** Using regex `split()` (e.g., `path.split(/[/\\]/).pop()`) inside `map` operations in high-frequency renders or large lists causes severe O(N) array allocation overhead, triggering excessive Garbage Collection pauses and degrading frame rate.
**Action:** Replace `split().pop()` or `split().slice().join()` on strings inside large list iterations with zero-allocation fallback strategies using standard primitive functions like `lastIndexOf()` and `substring()` to significantly reduce memory footprint and calculation overhead.

## 2024-05-01 - Consolidating Sequential Array Searches
**Learning:** In high-frequency React hooks (e.g., fallback searches during simulation ticks in `useGhostRunner`), executing multiple sequential `array.find()` operations or chaining `.filter().find()` over large unmemoized arrays causes severe CPU overhead and redundant array traversals. However, simply replacing a single native `.find()` or `.map()` with a `for` loop for micro-optimization harms readability and violates performance optimization principles if no measurable bottleneck exists.
**Action:** Replace multiple sequential `.find()` calls or `.filter().find()` chains with a single `O(N)` `for` loop that tracks fallbacks within the same pass. Do not replace single native array methods with loops merely for micro-optimization.

## 2024-05-02 - Optimize Array Searches in Simulation Hooks
**Learning:** In high-frequency React hooks (like simulation ticks), using array functional methods like `.find()` repeatedly over large datasets causes unnecessary intermediate memory allocations and functional callback overhead, hurting performance.
**Action:** Replace multiple `.find()` calls on large datasets during high-frequency simulation loops with explicit, zero-allocation imperative `for` loops with early exits.

## 2025-02-21 - Optimize Graph Data Filtering
**Learning:** In React hooks, calculating derived array state by chaining multiple `.filter()` and `.map()` operations over large datasets (like `allNodes` in `useGraphData`) creates hidden performance bottlenecks by generating intermediate arrays and triggering multiple O(N) passes.
**Action:** Replace multiple O(N) array method chains with a single iterative `for` loop that accumulates all required metrics in a single O(N) pass, significantly reducing CPU overhead and memory allocations.

## 2026-05-06 - Prevent Unnecessary Code Block Re-renders
**Learning:** Heavyweight syntax highlighting components (like `react-syntax-highlighter`) can cause significant CPU spikes if they re-render frequently during parent state changes, even when the underlying code hasn't changed.
**Action:** Wrap components rendering static code blocks in `React.memo()` to short-circuit the render cycle and prevent expensive syntax re-parsing when parent state updates.

## 2026-05-05 - Array slice over-fetching overhead in hooks
**Learning:** In React hooks that execute on rapid animation or simulation ticks (like `useGhostRunner`), chaining functional array operations such as `[...array.filter()].slice()` creates hidden performance bottlenecks. This forces the engine to clone the array and perform multiple O(N) evaluations, significantly increasing garbage collection pressure.
**Action:** Replace `.filter().slice()` chains inside high-frequency hooks with a standard `for` loop, populating a new array until a `break` condition on length is met. This avoids intermediate allocations and drops the execution time.
## 2025-02-21 - Optimize O(E * T) nested array iterations
**Learning:** In high-frequency React hooks (e.g., updating visuals on simulation ticks), using `.some()` to check array containment inside a `.map()` callback over a large list creates a severe O(E * T) performance bottleneck (where E is the number of edges and T is trail length).
**Action:** Pre-compute a `Set` from the smaller list before mapping over the larger list, converting the `.some()` operation into an O(1) `Set.has()` lookup and dropping the time complexity to O(E).

## 2026-05-10 - Array Iteration Chain Bottleneck Elimination in useGraphData.js
**Learning:** In React hooks (e.g., `useGraphData.js`), calculating derived array state or executing side effects by chaining functional array methods like `.filter().forEach()` and `.map()` over large datasets causes severe performance bottlenecks by generating intermediate arrays and triggering multiple O(N) passes.
**Action:** Replace these chains with a single imperative `for` loop to eliminate intermediate allocations and reduce iteration overhead to a single O(N) pass.


## 2024-05-18 - Optimize array searches with O(1) Lookup Maps
**Learning:** Replacing an `Array.prototype.find()` with an imperative `for` loop is an ineffective micro-optimization when the underlying issue is executing an `O(N)` search repeatedly. While a `for` loop removes callback overhead, it does not solve the time complexity bottleneck and actively harms code readability.
**Action:** When a React component frequently searches a large array by ID, pre-compute an `O(1)` Map at the data source level (e.g., inside a custom hook using `useMemo`) and pass it down as a prop. This provides a genuine performance improvement without sacrificing readability.

## 2026-05-21 - Array allocation overhead in Object.entries mapping
**Learning:** In React components that render frequently or map over large lists, constructing string summaries using `Object.entries(obj).map(([k, v]) => ...).join(', ')` creates hidden performance bottlenecks by allocating multiple intermediate arrays (one for entries, one for the mapped strings), which causes severe garbage collection pressure.
**Action:** Replace `Object.entries().map().join()` chains with a standard imperative `for...in` loop that incrementally builds the string, eliminating all intermediate array allocations and reducing CPU overhead during render cycles.

## 2026-05-23 - Optimize string suffix checks with tuple endswith
**Learning:** When checking if a string ends with one of multiple extensions, using `any(name.endswith(ext) for ext in supported)` creates unnecessary generator evaluation overhead. In Python, `str.endswith` (and `str.startswith`) inherently accept a tuple of strings and execute the check at the C level, making it significantly faster.
**Action:** Replace `any(string.endswith(ext) for ext in tuple_of_exts)` with `string.endswith(tuple_of_exts)` to eliminate generator allocation and loop overhead, especially in hot paths like file traversal.

## 2024-05-24 - Python AST Traversal Optimization Correction
**Learning:** When replacing Python's `ast.walk()` with a Breadth-First Search (BFS) queue for performance optimization, restricting child traversal to a hardcoded list of block attributes (like `body`, `orelse`, `handlers`) breaks static analysis by missing expressions (e.g., `ast.Call` inside `value` or `args` of a function call or list).
**Action:** Instead, use `queue.extend(ast.iter_child_nodes(node))` to safely iterate and enqueue all valid child nodes while still avoiding the generator overhead of `ast.walk()`.
## 2026-05-25 - Avoid `any()` generator expression overhead in hot paths
**Learning:** In performance-critical Python paths (e.g., frequent AST traversal loops in `analyst/analyzer.py`), using `any()` combined with a generator expression (e.g., `any(... for x in ...)` incurs significant overhead due to generator allocation.
**Action:** Replace `any()` with generator expressions with explicit, unrolled `for` loops containing an early `break`. This eliminates the generator allocation and reduces execution time.
## 2024-05-26 - Max function generator expression overhead
**Learning:** In performance-critical recursive functions (e.g., AST traversal in `analyst/analyzer.py`), passing a generator expression to `max()` (like `max((walk(g) for g in ast.iter_child_nodes()), default=0)`) causes severe performance degradation due to the overhead of allocating a new generator object on every single recursive call.
**Action:** Replace `max()` with generator expressions in recursive or high-frequency loops with explicit `for` loops tracking the maximum value. This eliminates the generator allocation overhead entirely.

## 2024-05-27 - Caching Data on Immutable React Props
**Learning:** In high-frequency UI components (like `SearchBar`), iterating over large datasets and modifying objects directly (e.g. `node._searchStr = ...`) to cache computed strings is a dangerous anti-pattern in React because it violates immutability rules. It triggers linting errors (`react-hooks/immutability`) and can cause subtle bugs or runtime errors if the objects are frozen.
**Action:** Instead of modifying the node objects directly, use a module-level `WeakMap` (`searchCache.set(node, searchStr)`) to associate the precomputed strings with the node references. This provides the performance benefit of caching while keeping the node props strictly immutable and avoiding memory leaks.


## 2024-05-28 - Optimize Graph Traversal Fallback with O(1) Sets
**Learning:** In graph traversal algorithms (like `build_learning_path`), repeatedly finding unvisited nodes inside a loop using an O(N) list comprehension like `[nid for nid in scored if nid not in visited]` creates a severe O(N²) time complexity bottleneck when the graph contains many isolated nodes or disconnected components.
**Action:** Replace the O(N) list comprehension with an O(1) tracking set. Initialize an `unvisited_set = set(all_nodes)` before the loop, and use `.discard(node_id)` whenever a node is visited. This reduces the fallback search to O(1) set operations, drastically improving performance on sparse or disconnected graphs.
## 2024-05-29 - Optimize dictionary copying and unpacking in list comprehensions
**Learning:** Using dictionary comprehensions (e.g., `{k: v for k, v in d.items() if k != 'key'}`) or dictionary unpacking (`{**d, 'key': val}`) inside high-frequency loops incurs significant overhead due to Python-level iteration and object allocation. However, blindly replacing them with in-place mutations (e.g., `d['key'] = val`) can introduce severe state mutation regressions.
**Action:** To safely optimize dictionary copying, use native C-optimized methods like `.copy()` and `.pop()`. When updating dictionaries inside a list comprehension, preserve immutability while eliminating unnecessary copying by conditionally applying the update (e.g., `[{**item, 'key': val} if item.get('key') != val else item for item in items]`). This securely reuses references when the value hasn't changed.
