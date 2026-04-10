import { useState, useEffect, useCallback, useRef, useMemo } from 'react';

const TRAIL_LENGTH = 4;
const DEFAULT_EDGE_STYLE = { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 };
const GHOST_ACTIVE_EDGE_STYLE = { stroke: '#f43f5e', strokeWidth: 7 };
const GHOST_TRAIL_EDGE_STYLE = { stroke: 'rgba(244, 63, 94, 0.5)', strokeWidth: 4 };

function isNavigableNode(node) {
    return Boolean(node?.data?.file);
}

// ─── Traversal Strategy Functions ─────────────────────────────────────
// Each receives ctx: { currentActiveId, nodes, edges, visitedSet, trail, nodesMap, degreeMap }
// Returns nextNodeId or null

function pickRandomFromPool(candidates) {
    const withFile = candidates.filter(isNavigableNode);
    const pool = withFile.length > 0 ? withFile : candidates;
    return pool[Math.floor(Math.random() * pool.length)] || null;
}

function getOutgoingTargets(ctx) {
    const { currentActiveId, edges, nodesMap } = ctx;
    return edges
        .filter(e => e.source === currentActiveId)
        .map(e => nodesMap.get(e.target))
        .filter(isNavigableNode);
}

function pickEntryPoint(ctx) {
    const { nodes, visitedSet } = ctx;
    const fileNodes = nodes.filter(isNavigableNode);
    const entries = fileNodes.filter(n => n.data?.entry_point);
    const unvisitedEntries = entries.filter(n => !visitedSet.has(n.id));
    if (unvisitedEntries.length > 0) return pickRandomFromPool(unvisitedEntries);
    if (entries.length > 0) return pickRandomFromPool(entries);
    return pickRandomFromPool(fileNodes);
}

function getBaseEdgeVisuals(edge) {
    const baseStyle = edge.data?.ghostBaseStyle || edge.style || DEFAULT_EDGE_STYLE;
    return {
        className: edge.data?.ghostBaseClassName ?? edge.className ?? '',
        animated: edge.data?.ghostBaseAnimated ?? false,
        style: { ...baseStyle },
    };
}

const strategies = {
    // ── Smart: Entry points → DFS, pause at hubs ──
    smart(ctx) {
        const { currentActiveId, nodes, nodesMap, visitedSet, dfsStackRef, degreeMap } = ctx;
        if (!currentActiveId) {
            // Start from an entry point
            const start = pickEntryPoint(ctx);
            if (start && dfsStackRef) dfsStackRef.current = [];
            return start?.id || null;
        }

        // Try unvisited outgoing edges first (DFS behavior)
        const targets = getOutgoingTargets(ctx);
        const unvisited = targets.filter(n => !visitedSet.has(n.id));

        if (unvisited.length > 0) {
            // If multiple unvisited, push others onto DFS stack
            if (dfsStackRef && unvisited.length > 1) {
                dfsStackRef.current.push(...unvisited.slice(1).map(n => n.id));
            }
            return unvisited[0].id;
        }

        // Backtrack: pop from DFS stack
        if (dfsStackRef && dfsStackRef.current.length > 0) {
            while (dfsStackRef.current.length > 0) {
                const backtrackId = dfsStackRef.current.pop();
                if (!visitedSet.has(backtrackId) && nodesMap.has(backtrackId)) {
                    return backtrackId;
                }
            }
        }

        // All reachable visited — jump to an unvisited node
        const allUnvisited = nodes.filter(n => !visitedSet.has(n.id) && n.data?.file);
        if (allUnvisited.length > 0) {
            // Prefer unvisited entry points, then hubs
            const unvisitedEntries = allUnvisited.filter(n => n.data?.entry_point);
            if (unvisitedEntries.length > 0) return unvisitedEntries[0].id;

            // Find highest degree unvisited node (hubs first)
            let bestUnvisited = null;
            let bestDegree = -1;
            for (let i = 0; i < allUnvisited.length; i++) {
                const n = allUnvisited[i];
                const degree = degreeMap.get(n.id) || 0;
                if (degree > bestDegree) {
                    bestDegree = degree;
                    bestUnvisited = n;
                }
            }
            return bestUnvisited?.id || null;
        }

        // Everything visited — pick random
        const picked = pickRandomFromPool(nodes);
        return picked?.id || null;
    },

    // ── Entry First: Start from entry points, DFS through call chain ──
    entryFirst(ctx) {
        const { currentActiveId, nodes, visitedSet, dfsStackRef, nodesMap } = ctx;
        if (!currentActiveId) {
            const start = pickEntryPoint(ctx);
            if (dfsStackRef) dfsStackRef.current = [];
            return start?.id || null;
        }

        const targets = getOutgoingTargets(ctx);
        const unvisited = targets.filter(n => !visitedSet.has(n.id));

        if (unvisited.length > 0) {
            if (dfsStackRef && unvisited.length > 1) {
                dfsStackRef.current.push(...unvisited.slice(1).map(n => n.id));
            }
            return unvisited[0].id;
        }

        if (dfsStackRef && dfsStackRef.current.length > 0) {
            while (dfsStackRef.current.length > 0) {
                const id = dfsStackRef.current.pop();
                if (!visitedSet.has(id) && nodesMap.has(id)) return id;
            }
        }

        // Jump to next unvisited entry point
        const nextEntry = nodes.find(n => n.data?.entry_point && !visitedSet.has(n.id));
        if (nextEntry) return nextEntry.id;

        // Any unvisited
        const any = nodes.find(n => !visitedSet.has(n.id) && n.data?.file);
        return any?.id || null;
    },

    // ── Hubs First: Visit most-connected nodes first ──
    hubsFirst(ctx) {
        const { currentActiveId, nodes, visitedSet, degreeMap } = ctx;
        if (!currentActiveId) {
            let bestUnvisited = null;
            let bestUnvisitedDegree = -1;
            let bestOverall = null;
            let bestOverallDegree = -1;

            for (let i = 0; i < nodes.length; i++) {
                const n = nodes[i];
                if (n.data?.file) {
                    const degree = degreeMap.get(n.id) || 0;
                    if (degree > bestOverallDegree) {
                        bestOverallDegree = degree;
                        bestOverall = n;
                    }
                    if (!visitedSet.has(n.id) && degree > bestUnvisitedDegree) {
                        bestUnvisitedDegree = degree;
                        bestUnvisited = n;
                    }
                }
            }
            return bestUnvisited?.id || bestOverall?.id || null;
        }

        // Follow edges, prefer higher-degree targets
        const targets = getOutgoingTargets(ctx);
        let bestTarget = null;
        let bestTargetDegree = -1;
        for (let i = 0; i < targets.length; i++) {
            const n = targets[i];
            if (!visitedSet.has(n.id)) {
                const degree = degreeMap.get(n.id) || 0;
                if (degree > bestTargetDegree) {
                    bestTargetDegree = degree;
                    bestTarget = n;
                }
            }
        }

        if (bestTarget) return bestTarget.id;

        // Jump to next highest-degree unvisited
        let bestUnvisited = null;
        let bestDegree = -1;
        for (let i = 0; i < nodes.length; i++) {
            const n = nodes[i];
            if (n.data?.file && !visitedSet.has(n.id)) {
                const degree = degreeMap.get(n.id) || 0;
                if (degree > bestDegree) {
                    bestDegree = degree;
                    bestUnvisited = n;
                }
            }
        }
        return bestUnvisited?.id || null;
    },

    // ── By File: Visit all nodes in one file before moving to the next ──
    byFile(ctx) {
        const { currentActiveId, nodes, visitedSet, nodesMap, fileQueueRef } = ctx;

        // Build file queue on first call or when empty
        if (!fileQueueRef || !fileQueueRef.current || fileQueueRef.current.length === 0) {
            const fileGroups = new Map();
            nodes.forEach(n => {
                const file = n.data?.file;
                if (file) {
                    if (!fileGroups.has(file)) fileGroups.set(file, []);
                    fileGroups.get(file).push(n.id);
                }
            });
            if (fileQueueRef) {
                fileQueueRef.current = Array.from(fileGroups.values()).flat();
            }
        }

        if (!currentActiveId && fileQueueRef) {
            // Start from first unvisited in queue
            const next = fileQueueRef.current.find(id => !visitedSet.has(id));
            return next || null;
        }

        // Try to stay in same file
        const currentFile = nodesMap.get(currentActiveId)?.data?.file;
        if (currentFile) {
            const sameFileUnvisited = nodes.filter(
                n => n.data?.file === currentFile && !visitedSet.has(n.id)
            );
            // Prefer connected nodes in same file
            const targets = getOutgoingTargets(ctx);
            const sameFileTargets = targets.filter(
                n => n.data?.file === currentFile && !visitedSet.has(n.id)
            );
            if (sameFileTargets.length > 0) return sameFileTargets[0].id;
            if (sameFileUnvisited.length > 0) return sameFileUnvisited[0].id;
        }

        // Move to next file
        if (fileQueueRef) {
            const next = fileQueueRef.current.find(id => !visitedSet.has(id));
            return next || null;
        }
        return null;
    },

    // ── Random: Original behavior ──
    random(ctx) {
        const { currentActiveId, nodes } = ctx;
        if (!currentActiveId) {
            const picked = pickRandomFromPool(nodes);
            return picked?.id || null;
        }

        const targets = getOutgoingTargets(ctx);
        if (targets.length > 0) {
            const picked = pickRandomFromPool(targets);
            return picked?.id || null;
        }

        const picked = pickRandomFromPool(nodes);
        return picked?.id || null;
    },
};

// ─── Hook ─────────────────────────────────────────────────────────────

export function useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode) {
    // Ghost Runner State
    const [isPlaying, setIsPlaying] = useState(false);
    const [activeNodeId, setActiveNodeId] = useState(null);
    const [stepCount, setStepCount] = useState(0);
    const [speed, setSpeed] = useState(2500);
    const [currentLabel, setCurrentLabel] = useState('');
    const [strategy, setStrategy] = useState('smart');
    const [mode, setMode] = useState('auto'); // 'auto' | 'explore'
    const [availableNextNodes, setAvailableNextNodes] = useState([]);
    const [narration, setNarration] = useState(null);

    // Refs for Game Loop
    const nodesRef = useRef([]);
    const nodesMapRef = useRef(new Map());
    const edgesRef = useRef([]);
    const activeNodeIdRef = useRef(null);
    const trailRef = useRef([]);
    const visitedSetRef = useRef(new Set());
    const dfsStackRef = useRef([]);
    const fileQueueRef = useRef([]);
    const narrationRequestIdRef = useRef(0);

    useEffect(() => {
        nodesRef.current = nodes;
        nodesMapRef.current = new Map(nodes.map(n => [n.id, n]));
    }, [nodes]);
    useEffect(() => { edgesRef.current = edges; }, [edges]);
    useEffect(() => { activeNodeIdRef.current = activeNodeId; }, [activeNodeId]);

    // Compute degree map when edges change
    const degreeMap = useMemo(() => {
        const map = new Map();
        edges.forEach(e => {
            map.set(e.source, (map.get(e.source) || 0) + 1);
            map.set(e.target, (map.get(e.target) || 0) + 1);
        });
        return map;
    }, [edges]);

    const degreeMapRef = useRef(degreeMap);
    useEffect(() => { degreeMapRef.current = degreeMap; }, [degreeMap]);

    // PERFORMANCE OPTIMIZATION (Bolt): Prevent O(N) re-render bottleneck on non-tick UI updates
    // by memoizing the array filters. stepCount acts as the trigger to re-evaluate the visited set.
    const visitedCount = useMemo(() => {
        return nodes.filter((node) => isNavigableNode(node) && visitedSetRef.current.has(node.id)).length;
    }, [nodes, stepCount]); // eslint-disable-line react-hooks/exhaustive-deps -- stepCount is an intentional reactive trigger to re-read visitedSetRef.current after each step advance
    // Encode only the fields that affect navigability into a stable key, so totalNodes is not
    // invalidated on every tick-driven nodes array replacement (only when graph structure changes).
    const navigableNodesKey = useMemo(
        () => nodes.map((node) => `${node.id}:${node?.data?.file ? 1 : 0}`).join('|'),
        [nodes]
    );
    // isNavigableNode ≡ Boolean(node?.data?.file), which the key encodes as `:1`. Counting those
    // entries directly removes any `nodes` reference and keeps the dependency array complete.
    const totalNodes = useMemo(
        () => navigableNodesKey.split('|').filter((s) => s.endsWith(':1')).length,
        [navigableNodesKey]
    );

    // ── Narration fetcher (non-blocking) ──
    const fetchNarration = useCallback((nodeId, previousNodeId) => {
        const requestId = ++narrationRequestIdRef.current;
        const node = nodesMapRef.current.get(nodeId);
        if (!node?.data?.file) return;

        fetch('/api/ghost-narrate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                node_id: nodeId,
                file_path: node.data.file,
                previous_node_id: previousNodeId,
                strategy,
                context_nodes: trailRef.current.slice(0, 3),
            }),
        })
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                // Only apply if ghost hasn't moved past this node
                if (data && narrationRequestIdRef.current === requestId) {
                    setNarration(data);
                }
            })
            .catch(() => { /* narration is optional, fail silently */ });
    }, [strategy]);

    // ── Apply visual classes to nodes and edges ──
    const applyVisuals = useCallback((newTrail, previousId, nextId) => {
        const visited = visitedSetRef.current;

        setNodes(nds => nds.map(node => {
            const trailIndex = newTrail.indexOf(node.id);
            let className = node.data?.isExternal ? 'external-ref' : '';

            if (trailIndex === 0) className += ' ghost-active';
            else if (trailIndex === 1) className += ' ghost-trail-1';
            else if (trailIndex === 2) className += ' ghost-trail-2';
            else if (trailIndex >= 3) className += ' ghost-trail-3';
            else if (visited.has(node.id)) className += ' ghost-visited';

            className = className.trim();

            // PERFORMANCE OPTIMIZATION (Bolt): Prevent React Flow O(N) re-renders
            if (node.className === className) return node;
            return { ...node, className };
        }));

        if (previousId && nextId) {
            const trailEdgePairs = [];
            for (let i = 0; i < newTrail.length - 1; i++) {
                trailEdgePairs.push({ from: newTrail[i + 1], to: newTrail[i] });
            }

            setEdges(eds => eds.map(edge => {
                const isActive = edge.source === previousId && edge.target === nextId;
                const isTrail = trailEdgePairs.some(p => edge.source === p.from && edge.target === p.to);

                const baseVisuals = getBaseEdgeVisuals(edge);
                let className = baseVisuals.className;
                let style = baseVisuals.style;
                let animated = baseVisuals.animated;

                if (isActive) {
                    className = 'ghost-edge-active';
                    style = GHOST_ACTIVE_EDGE_STYLE;
                    animated = true;
                } else if (isTrail) {
                    className = 'ghost-edge-trail';
                    style = GHOST_TRAIL_EDGE_STYLE;
                    animated = false;
                }

                // PERFORMANCE OPTIMIZATION (Bolt): Prevent React Flow O(N) re-renders
                const isUnchanged = edge.className === className &&
                    edge.animated === animated &&
                    edge.style?.stroke === style.stroke &&
                    edge.style?.strokeWidth === style.strokeWidth &&
                    edge.style?.strokeDasharray === style.strokeDasharray;

                if (isUnchanged) return edge;
                return { ...edge, className, style, animated };
            }));
        }
    }, [setNodes, setEdges]);

    // ── Explore mode: user chooses next node ──
    const onUserChooseNext = useCallback((nodeId) => {
        if (mode !== 'explore') return;

        const currentActiveId = activeNodeIdRef.current;
        const nodesMap = nodesMapRef.current;
        const trail = trailRef.current;

        const nextNode = nodesMap.get(nodeId);
        if (!isNavigableNode(nextNode)) return;

        const newTrail = [nodeId, ...trail.filter(id => id !== nodeId)].slice(0, TRAIL_LENGTH);
        trailRef.current = newTrail;
        visitedSetRef.current.add(nodeId);

        setActiveNodeId(nodeId);
        setStepCount(prev => prev + 1);

        setCurrentLabel(nextNode?.data?.label || '');

        setCodePanelNode(nextNode);

        // Fetch narration
        fetchNarration(nodeId, currentActiveId);

        // Update visuals
        applyVisuals(newTrail, currentActiveId, nodeId);

        // Compute next available choices
        const nextTargets = getOutgoingTargets({
            currentActiveId: nodeId,
            edges: edgesRef.current,
            nodesMap,
        });
        setAvailableNextNodes(nextTargets);
    }, [mode, setCodePanelNode, fetchNarration, applyVisuals]);

    // ── Main Game Loop ──
    useEffect(() => {
        let timeoutId;

        const tick = () => {
            if (!isPlaying) return;

            const currentNodes = nodesRef.current;
            const currentNodesMap = nodesMapRef.current;
            const currentEdges = edgesRef.current;
            const currentActiveId = activeNodeIdRef.current;
            const trail = trailRef.current;

            if (currentNodes.length === 0) return;

            // In explore mode: compute choices and wait
            if (mode === 'explore') {
                if (!currentActiveId) {
                    // Auto-pick first node in explore mode
                    const ctx = {
                        currentActiveId: null,
                        nodes: currentNodes,
                        edges: currentEdges,
                        visitedSet: visitedSetRef.current,
                        trail,
                        nodesMap: currentNodesMap,
                        degreeMap: degreeMapRef.current,
                        dfsStackRef,
                        fileQueueRef,
                    };
                    const startId = strategies[strategy]?.(ctx) || strategies.smart(ctx);
                    if (startId) onUserChooseNext(startId);
                } else {
                    // Show available choices
                    const targets = getOutgoingTargets({
                        currentActiveId,
                        edges: currentEdges,
                        nodesMap: currentNodesMap,
                    });
                    setAvailableNextNodes(targets);
                }
                return; // Don't auto-advance
            }

            // Auto mode: use strategy
            const ctx = {
                currentActiveId,
                nodes: currentNodes,
                edges: currentEdges,
                visitedSet: visitedSetRef.current,
                trail,
                nodesMap: currentNodesMap,
                degreeMap: degreeMapRef.current,
                dfsStackRef,
                fileQueueRef,
            };

            const strategyFn = strategies[strategy] || strategies.smart;
            const nextNodeId = strategyFn(ctx);

            if (!nextNodeId) {
                // All nodes visited or no valid next — stop
                setIsPlaying(false);
                setAvailableNextNodes([]);
                return;
            }

            const newTrail = [nextNodeId, ...trail.filter(id => id !== nextNodeId)].slice(0, TRAIL_LENGTH);
            trailRef.current = newTrail;
            const nextNode = currentNodesMap.get(nextNodeId);
            if (!isNavigableNode(nextNode)) {
                setIsPlaying(false);
                setAvailableNextNodes([]);
                return;
            }

            visitedSetRef.current.add(nextNodeId);

            setActiveNodeId(nextNodeId);
            setStepCount(prev => prev + 1);
            setCurrentLabel(nextNode?.data?.label || '');

            setCodePanelNode(nextNode);

            // Narration: rate-limit based on speed
            const shouldNarrate = speed >= 2500 || // Slow/Normal: every step
                (speed < 2500 && visitedSetRef.current.size % 2 === 0); // Fast: every 2nd
            if (shouldNarrate) {
                fetchNarration(nextNodeId, currentActiveId);
            }

            applyVisuals(newTrail, currentActiveId, nextNodeId);

            // Hub pause: slow down at highly-connected nodes (smart strategy)
            const nodeDegree = degreeMapRef.current.get(nextNodeId) || 0;
            const effectiveSpeed = (strategy === 'smart' && nodeDegree > 3) ? speed * 1.5 : speed;

            timeoutId = setTimeout(tick, effectiveSpeed);
        };

        if (isPlaying && nodesRef.current.length > 0) {
            tick();
        }

        return () => clearTimeout(timeoutId);
    }, [isPlaying, speed, strategy, mode, setNodes, setEdges, setCodePanelNode, applyVisuals, fetchNarration, onUserChooseNext]);

    // Reset visuals when stopping
    useEffect(() => {
        if (!isPlaying) {
            setNodes(nds => nds.map(n => {
                const className = n.data?.isExternal ? 'external-ref' :
                    visitedSetRef.current.has(n.id) ? 'ghost-visited' : '';
                if (n.className === className) return n;
                return { ...n, className };
            }));
            setEdges(eds => eds.map(e => ({
                ...e,
                ...getBaseEdgeVisuals(e),
            })));
            setAvailableNextNodes([]);
        }
    }, [isPlaying, setNodes, setEdges]);

    const onResetSimulation = useCallback(() => {
        setIsPlaying(false);
        setActiveNodeId(null);
        setStepCount(0);
        setCurrentLabel('');
        trailRef.current = [];
        visitedSetRef.current = new Set();
        dfsStackRef.current = [];
        fileQueueRef.current = [];
        setAvailableNextNodes([]);
        setNarration(null);
        narrationRequestIdRef.current = 0;
    }, []);

    // Generate run summary from visited data
    const runSummary = useMemo(() => {
        if (isPlaying) return null;

        const visited = visitedSetRef.current;
        if (visited.size === 0) return null;

        const visitedNodes = nodes.filter(n => isNavigableNode(n) && visited.has(n.id));
        const filesVisited = new Set(visitedNodes.map(n => n.data?.file).filter(Boolean));
        const unvisitedEntries = nodes.filter(
            (n) => isNavigableNode(n) && n.data?.entry_point && !visited.has(n.id)
        );

        // Most connected visited node
        let mostConnected = null;
        let maxDegree = 0;
        visitedNodes.forEach(n => {
            const d = degreeMap.get(n.id) || 0;
            if (d > maxDegree) { maxDegree = d; mostConnected = n; }
        });

        return {
            visitedCount: visitedNodes.length,
            totalNodes: nodes.filter(isNavigableNode).length,
            filesVisited: filesVisited.size,
            mostConnected: mostConnected ? { label: mostConnected.data?.label, degree: maxDegree } : null,
            unvisitedEntries: unvisitedEntries.map(n => n.data?.label).filter(Boolean),
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- stepCount forces recalc when visitedSetRef changes
    }, [nodes, degreeMap, stepCount, isPlaying]);

    return {
        isPlaying,
        setIsPlaying,
        stepCount,
        setStepCount,
        speed,
        setSpeed,
        currentLabel,
        setCurrentLabel,
        onResetSimulation,
        activeNodeId,
        setActiveNodeId,
        trailRef,
        // New Phase 1+ exports
        strategy,
        setStrategy,
        mode,
        setMode,
        visitedCount,
        totalNodes,
        availableNextNodes,
        onUserChooseNext,
        narration,
        setNarration,
        runSummary,
        degreeMap,
    };
}
