import { useState, useEffect, useMemo, useCallback } from 'react';
import { getLayoutedElements } from '../utils/layout';

const GRAPH_CACHE_SCHEMA_VERSION = 2;
const GRAPH_CACHE_SOURCE = 'user_upload';

function getInitialSelectedFile(nodes) {
    const filesSet = new Set();
    let entryFile = null;

    nodes.forEach((node) => {
        const file = node.data?.file;
        if (!file) {
            return;
        }

        filesSet.add(file);
        if (node.data?.entry_point && !entryFile) {
            entryFile = file;
        }
    });

    return entryFile || [...filesSet][0] || null;
}

function readCachedGraph(cacheKey) {
    const emptyGraph = {
        nodes: [],
        edges: [],
        fileDependencies: null,
        selectedFile: null,
    };

    try {
        const cached = localStorage.getItem(cacheKey);
        if (!cached) {
            return emptyGraph;
        }

        const {
            schemaVersion,
            source,
            nodes,
            edges,
            fileDependencies,
        } = JSON.parse(cached);

        if (schemaVersion !== GRAPH_CACHE_SCHEMA_VERSION || source !== GRAPH_CACHE_SOURCE) {
            localStorage.removeItem(cacheKey);
            return emptyGraph;
        }

        const safeNodes = Array.isArray(nodes) ? nodes : [];
        const safeEdges = Array.isArray(edges) ? edges : [];
        const safeDependencies = Array.isArray(fileDependencies) ? fileDependencies : null;

        return {
            nodes: safeNodes,
            edges: safeEdges,
            fileDependencies: safeDependencies,
            selectedFile: getInitialSelectedFile(safeNodes),
        };
    } catch {
        localStorage.removeItem(cacheKey);
        return emptyGraph;
    }
}

export function useGraphData(setNodes, setEdges) {
    const cacheKey = 'vg_v1_graph';
    const [initialGraph] = useState(() => readCachedGraph(cacheKey));

    // All graph data (unfiltered)
    const [allNodes, setAllNodes] = useState(initialGraph.nodes);
    const [allEdges, setAllEdges] = useState(initialGraph.edges);
    const [fileDependencies, setFileDependencies] = useState(initialGraph.fileDependencies);

    // File selection
    const [selectedFile, setSelectedFile] = useState(initialGraph.selectedFile);

    // Compute file list and stats
    const { files, nodeStats } = useMemo(() => {
        const statsMap = {};
        allNodes.forEach(n => {
            const f = n.data?.file || '_external';
            if (!statsMap[f]) statsMap[f] = { count: 0, hasEntry: false, types: {} };
            statsMap[f].count++;
            if (n.data?.entry_point) statsMap[f].hasEntry = true;
            const t = n.data?.type || 'default';
            statsMap[f].types[t] = (statsMap[f].types[t] || 0) + 1;
        });

        const fileList = Object.keys(statsMap).sort((a, b) => {
            if (statsMap[a].hasEntry && !statsMap[b].hasEntry) return -1;
            if (!statsMap[a].hasEntry && statsMap[b].hasEntry) return 1;
            return a.localeCompare(b);
        });

        return { files: fileList, nodeStats: statsMap };
    }, [allNodes]);

    const handleUploadSuccess = useCallback((result, resetGhostStateCallback) => {
        const { nodes: newNodes, edges: newEdges, file_dependencies: newFileDependencies } = result;
        const safeNodes = Array.isArray(newNodes) ? newNodes : [];
        const safeEdges = Array.isArray(newEdges) ? newEdges : [];

        if (safeNodes.length === 0) {
            setSelectedFile(null);
            setAllNodes([]);
            setAllEdges([]);
            setFileDependencies(null);
            setNodes([]);
            setEdges([]);
            localStorage.removeItem(cacheKey);

            if (resetGhostStateCallback) {
                resetGhostStateCallback();
            }
            return;
        }

        // Process nodes to match the "custom" type and add metadata
        const customNodes = safeNodes.map(n => ({
            ...n,
            type: 'custom',
            data: {
                ...n.data,
                file: n.data.file || n.data.original_data?.file || null,
                lineno: n.data.lineno || n.data.original_data?.lineno,
                entry_point: n.data.entry_point || false,
            }
        }));

        // Auto-select the first file from the new project
        const filesSet = new Set();
        customNodes.forEach(n => {
            if (n.data.file) filesSet.add(n.data.file);
        });

        const newFiles = [...filesSet];
        setSelectedFile(newFiles[0] || null);

        setAllNodes(customNodes);
        setAllEdges(safeEdges);
        setFileDependencies(Array.isArray(newFileDependencies) ? newFileDependencies : null);

        try {
            localStorage.setItem(
                cacheKey,
                JSON.stringify({
                    schemaVersion: GRAPH_CACHE_SCHEMA_VERSION,
                    source: GRAPH_CACHE_SOURCE,
                    nodes: customNodes,
                    edges: safeEdges,
                    fileDependencies: Array.isArray(newFileDependencies) ? newFileDependencies : null,
                })
            );
        } catch { /* ignore */ }

        // Provide a callback to reset external state (like ghost runner, selections)
        if (resetGhostStateCallback) {
            resetGhostStateCallback();
        }
    }, [cacheKey, setAllNodes, setAllEdges, setEdges, setNodes, setSelectedFile]);

    // Filter nodes/edges when file selection changes
    useEffect(() => {
        if (allNodes.length === 0) {
            setNodes([]);
            setEdges([]);
            return;
        }

        // Show all nodes when no file is selected
        if (!selectedFile) {
            const layouted = getLayoutedElements(
                allNodes.map(n => ({ ...n })),
                allEdges
            );
            setNodes(layouted.nodes);
            setEdges(layouted.edges);
            return;
        }

        const fileNodeIds = new Set();
        const fileNodes = allNodes.filter(n => {
            const nFile = n.data?.file || '_external';
            if (nFile === selectedFile) {
                fileNodeIds.add(n.id);
                return true;
            }
            return false;
        });

        const relevantEdges = allEdges.filter(e =>
            fileNodeIds.has(e.source) || fileNodeIds.has(e.target)
        );

        const externalNodeIds = new Set();
        relevantEdges.forEach(e => {
            if (!fileNodeIds.has(e.source)) externalNodeIds.add(e.source);
            if (!fileNodeIds.has(e.target)) externalNodeIds.add(e.target);
        });

        const externalNodes = allNodes
            .filter(n => externalNodeIds.has(n.id))
            .map(n => ({
                ...n,
                className: 'external-ref',
                data: { ...n.data, isExternal: true },
            }));

        const combinedNodes = [...fileNodes, ...externalNodes];

        const styledEdges = relevantEdges.map(e => {
            const isInternal = fileNodeIds.has(e.source) && fileNodeIds.has(e.target);
            const isCycle = e.data?.is_cycle_edge === true;

            if (isCycle) {
                const style = { stroke: '#f97316', strokeWidth: 3, strokeDasharray: '8 4' };
                return {
                    ...e,
                    style,
                    animated: true,
                    className: 'cycle-edge',
                    label: '\u27F3',
                    labelStyle: { fill: '#f97316', fontSize: 12 },
                    data: {
                        ...e.data,
                        ghostBaseClassName: 'cycle-edge',
                        ghostBaseAnimated: true,
                        ghostBaseStyle: style,
                    },
                };
            }

            const style = isInternal
                ? { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 }
                : { stroke: 'rgba(148, 163, 184, 0.25)', strokeWidth: 2, strokeDasharray: '6 4' };
            const className = isInternal ? '' : 'external-edge';
            return {
                ...e,
                style,
                animated: false,
                className,
                data: {
                    ...e.data,
                    ghostBaseClassName: className,
                    ghostBaseAnimated: false,
                    ghostBaseStyle: style,
                },
            };
        });

        const layouted = getLayoutedElements(
            combinedNodes.map(n => ({ ...n })),
            styledEdges
        );

        setNodes(layouted.nodes);
        setEdges(layouted.edges);
    }, [selectedFile, allNodes, allEdges, setNodes, setEdges]);

    // PERFORMANCE OPTIMIZATION (Bolt): Compute degree map here based on the filtered subgraph (`relevantEdges`),
    // rather than in useGhostRunner where `edges` changes visually every animation tick.
    // This perfectly preserves the localized hub logic while completely eliminating O(E) redundant Map allocations.
    const currentDegreeMap = useMemo(() => {
        const dMap = new Map();
        if (allNodes.length === 0 || !allEdges) return dMap;

        let edgesToCount = allEdges;
        if (selectedFile) {
            const fileNodeIds = new Set();
            allNodes.forEach(n => {
                const nFile = n.data?.file || '_external';
                if (nFile === selectedFile) fileNodeIds.add(n.id);
            });
            edgesToCount = allEdges.filter(e => fileNodeIds.has(e.source) || fileNodeIds.has(e.target));
        }

        edgesToCount.forEach(e => {
            dMap.set(e.source, (dMap.get(e.source) || 0) + 1);
            dMap.set(e.target, (dMap.get(e.target) || 0) + 1);
        });
        return dMap;
    }, [selectedFile, allNodes, allEdges]);

    return {
        allNodes,
        selectedFile,
        setSelectedFile,
        files,
        nodeStats,
        fileDependencies,
        handleUploadSuccess,
        currentDegreeMap
    };
}
