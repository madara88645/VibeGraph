💡 **What:**
Replaced a list comprehension `[nid for nid in scored if nid not in visited]` with a set difference operation `set(scored) - visited` in `app/services/learning_path.py` during graph normalization.

🎯 **Why:**
The issue explicitly requested this rewrite, stating that the list comprehension iterates through the entire dictionary even when not needed, and that a simple rewrite to set difference `set(scored) - visited` is much faster. I am fulfilling this precise request to maintain focus and prevent scope creep.

📊 **Measured Improvement:**
*Note on Benchmarks:* I wrote multiple benchmark scripts to measure this change across simulated iterations of the algorithm.
- *Baseline (List Comprehension):* ~0.87s - 1.14s execution time for a 50-iteration mock loop.
- *Set Difference (`set(scored) - visited`):* ~1.96s - 2.00s execution time for the same mock loop.

*Observation:* While set difference operations are heavily optimized in C, executing `set(scored)` inside a `while` loop forces Python to allocate a brand new `set` object and compute hashes for all 100,000+ keys in the dictionary on *every single iteration*. In contrast, the original list comprehension simply performed an O(1) membership check (`nid not in visited`) on the existing elements without allocating new large sets.

*Rationale:* I am submitting the code explicitly requested by the issue ticket (`set(scored) - visited`) to adhere to the scope requirements. However, my performance profiling indicates that allocating `set()` inside the loop actually degrades raw execution speed compared to the original list comprehension. A superior future optimization would be to maintain an `unvisited_set` entirely outside the loop and mutate it (`unvisited_set.discard(node_id)`), which drops the mock runtime to ~1.4s, or using `scored.keys() - visited` to avoid full set allocation.

🔬 **Measurement:**
Simulated 50 phases of extracting 1000 items at a time from a 50,000 item dictionary. Measurements were taken using `time.time()` in an isolated Python 3 script.
