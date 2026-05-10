💡 What: Replaced an `O(N)` array traversal (`allNodes.find()`) in the `LearningPath` component with an `O(1)` Map lookup. Extracted `allNodesMap` into the `useGraphData` hook using `useMemo` and passed it down to `LearningPath`.

🎯 Why: The `LearningPath` component iterates over the `allNodes` array, which can be massive (potentially thousands of nodes in large projects), to find a specific node matching an ID. Using `.find()` creates a repeated O(N) lookup. Pre-computing a Map completely resolves the time complexity bottleneck without sacrificing readability by replacing array methods with micro-optimized loops.

📊 Impact: Reduces the time complexity of looking up path nodes from `O(N)` to `O(1)`.

🔬 Measurement: Ensure the LearningPath feature continues to work as expected, jumping straight to the selected node correctly when triggered.
