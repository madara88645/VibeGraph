import { useState, useEffect, useMemo, useCallback } from 'react';
import { getLayoutedElements } from '../utils/layout';

export function useGraphData(setNodes, setEdges) {
    // All graph data (unfiltered)
    const [allNodes, setAllNodes] = useState([]);
    const [allEdges, setAllEdges] = useState([]);

    // File selection
    const [selectedFile, setSelectedFile] = useState(null);

    // Load graph data
    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/graph_data.json');
                if (!response.ok) return;
                const data = await response.json();

                const customNodes = data.nodes.map(n => ({
                    ...n,
                    type: 'custom',
                    data: {
                        ...n.data,
                        file: n.data.file || n.data.original_data?.file || null,
                        lineno: n.data.lineno || n.data.original_data?.lineno,
                        entry_point: n.data.entry_point || false,
                    }
                }));

                setAllNodes(customNodes);
                setAllEdges(data.edges);

                // Auto-select first file that has an entry point, or just the first file
                const filesSet = new Set();
                let entryFile = null;
                customNodes.forEach(n => {
                    const f = n.data.file;
                    if (f) {
                        filesSet.add(f);
                        if (n.data.entry_point && !entryFile) entryFile = f;
                    }
                });
                setSelectedFile(entryFile || [...filesSet][0] || null);

            } catch (error) {
                console.error("Failed to fetch graph data:", error);
            }
        };
        fetchData();
    }, []);

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
        const { nodes: newNodes, edges: newEdges } = result;

        // Process nodes to match the "custom" type and add metadata
        const customNodes = newNodes.map(n => ({
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
        if (newFiles.length > 0) {
            setSelectedFile(newFiles[0]);
        }

        setAllNodes(customNodes);
        setAllEdges(newEdges);

        // Provide a callback to reset external state (like ghost runner, selections)
        if (resetGhostStateCallback) {
            resetGhostStateCallback();
        }
    }, [setAllNodes, setAllEdges, setSelectedFile]);

    // Filter nodes/edges when file selection changes
    useEffect(() => {
        if (allNodes.length === 0) return;

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
            return {
                ...e,
                style: isInternal
                    ? { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 }
                    : { stroke: 'rgba(148, 163, 184, 0.25)', strokeWidth: 2, strokeDasharray: '6 4' },
                animated: false,
                className: isInternal ? '' : 'external-edge',
            };
        });

        const layouted = getLayoutedElements(
            combinedNodes.map(n => ({ ...n })),
            styledEdges
        );

        setNodes(layouted.nodes);
        setEdges(layouted.edges);
    }, [selectedFile, allNodes, allEdges, setNodes, setEdges]);

    return {
        allNodes,
        selectedFile,
        setSelectedFile,
        files,
        nodeStats,
        handleUploadSuccess
    };
}
