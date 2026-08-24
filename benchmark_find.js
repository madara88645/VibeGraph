const { performance } = require('perf_hooks');

const NUM_NODES = 10000;
const nodes = [];
const visitedSet = new Set();

for (let i = 0; i < NUM_NODES; i++) {
    nodes.push({
        id: `node-${i}`,
        data: {
            file: `/path/to/file-${i}`,
            entry_point: i === NUM_NODES - 1 // Only the very last node is an entry point
        }
    });
}

// Baseline: unoptimized nodes.find
const baselineStart = performance.now();
for (let i = 0; i < 1000; i++) {
    nodes.find(n => n.data?.entry_point && !visitedSet.has(n.id));
}
const baselineEnd = performance.now();
console.log(`Baseline (1000 iterations): ${(baselineEnd - baselineStart).toFixed(2)}ms`);

// Cached approach
const entryPoints = nodes.filter(n => n.data?.entry_point);

const optimizedStart = performance.now();
for (let i = 0; i < 1000; i++) {
    entryPoints.find(n => !visitedSet.has(n.id));
}
const optimizedEnd = performance.now();
console.log(`Optimized (1000 iterations): ${(optimizedEnd - optimizedStart).toFixed(2)}ms`);

const speedup = (baselineEnd - baselineStart) / (optimizedEnd - optimizedStart);
console.log(`Speedup: ${speedup.toFixed(2)}x`);
