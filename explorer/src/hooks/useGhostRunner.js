import { useState, useEffect, useCallback, useRef } from 'react';

const TRAIL_LENGTH = 4;

export function useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode) {
    // Ghost Runner State
    const [isPlaying, setIsPlaying] = useState(false);
    const [activeNodeId, setActiveNodeId] = useState(null);
    const [stepCount, setStepCount] = useState(0);
    const [speed, setSpeed] = useState(2500);
    const [currentLabel, setCurrentLabel] = useState('');

    // Refs for Game Loop
    const nodesRef = useRef([]);
    const nodesMapRef = useRef(new Map());
    const edgesRef = useRef([]);
    const activeNodeIdRef = useRef(null);
    const trailRef = useRef([]);

    useEffect(() => {
        nodesRef.current = nodes;
        nodesMapRef.current = new Map(nodes.map(n => [n.id, n]));
    }, [nodes]);
    useEffect(() => { edgesRef.current = edges; }, [edges]);
    useEffect(() => { activeNodeIdRef.current = activeNodeId; }, [activeNodeId]);

    // Ghost Runner Loop
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

            const currentNode = currentActiveId ? currentNodesMap.get(currentActiveId) : null;
            let nextNodeId;

            const pickRandom = (candidates) => {
                const withFile = candidates.filter(n => n.data?.file);
                const pool = withFile.length > 0 ? withFile : candidates;
                return pool[Math.floor(Math.random() * pool.length)];
            };

            if (!currentNode) {
                const picked = pickRandom(currentNodes);
                nextNodeId = picked?.id;
            } else {
                const connectedEdges = currentEdges.filter(e => e.source === currentActiveId);
                if (connectedEdges.length > 0) {
                    const targetNodes = connectedEdges
                        .map(e => currentNodesMap.get(e.target))
                        .filter(Boolean);
                    const withFile = targetNodes.filter(n => n.data?.file);
                    const pool = withFile.length > 0 ? withFile : targetNodes;
                    const picked = pool[Math.floor(Math.random() * pool.length)];
                    nextNodeId = picked?.id;
                } else {
                    const picked = pickRandom(currentNodes);
                    nextNodeId = picked?.id;
                }
            }

            const newTrail = [nextNodeId, ...trail.filter(id => id !== nextNodeId)].slice(0, TRAIL_LENGTH);
            trailRef.current = newTrail;

            setActiveNodeId(nextNodeId);
            setStepCount(prev => prev + 1);

            const nextNode = currentNodesMap.get(nextNodeId);
            setCurrentLabel(nextNode?.data?.label || '');

            if (nextNode && nextNode.data?.file) {
                setCodePanelNode(nextNode);
            }

            setNodes(nds => nds.map(node => {
                const trailIndex = newTrail.indexOf(node.id);
                let className = node.data?.isExternal ? 'external-ref' : '';
                if (trailIndex === 0) className += ' ghost-active';
                else if (trailIndex === 1) className += ' ghost-trail-1';
                else if (trailIndex === 2) className += ' ghost-trail-2';
                else if (trailIndex >= 3) className += ' ghost-trail-3';

                className = className.trim();
                if (node.className === className) return node;
                return { ...node, className };
            }));

            if (currentActiveId && nextNodeId) {
                const trailEdgePairs = [];
                for (let i = 0; i < newTrail.length - 1; i++) {
                    trailEdgePairs.push({ from: newTrail[i + 1], to: newTrail[i] });
                }

                setEdges(eds => eds.map(edge => {
                    const isActive = edge.source === currentActiveId && edge.target === nextNodeId;
                    const isTrail = trailEdgePairs.some(p => edge.source === p.from && edge.target === p.to);

                    let className = '';
                    let style = { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 };
                    let animated = false;

                    if (isActive) {
                        className = 'ghost-edge-active';
                        style = { stroke: '#f43f5e', strokeWidth: 7 };
                        animated = true;
                    } else if (isTrail) {
                        className = 'ghost-edge-trail';
                        style = { stroke: 'rgba(244, 63, 94, 0.5)', strokeWidth: 4 };
                    }

                    if (edge.className === className && edge.animated === animated) return edge;
                    return { ...edge, className, style, animated };
                }));
            }

            timeoutId = setTimeout(tick, speed);
        };

        if (isPlaying && nodesRef.current.length > 0) {
            tick();
        }

        return () => clearTimeout(timeoutId);
    }, [isPlaying, speed, setNodes, setEdges, setCodePanelNode]);

    // Reset visuals when stopping
    useEffect(() => {
        if (!isPlaying) {
            setNodes(nds => nds.map(n => {
                const className = n.data?.isExternal ? 'external-ref' : '';
                if (n.className === className) return n;
                return { ...n, className };
            }));
            setEdges(eds => eds.map(e => {
                const animated = false;
                const className = e.className?.includes('external-edge') ? 'external-edge' : '';

                if (e.className === className && e.animated === animated) return e;

                return {
                    ...e, animated,
                    className,
                    style: e.className?.includes('external-edge')
                        ? { stroke: 'rgba(148, 163, 184, 0.2)', strokeWidth: 1.5, strokeDasharray: '5 3' }
                        : { stroke: 'rgba(148, 163, 184, 0.5)', strokeWidth: 2.5 }
                };
            }));
        }
    }, [isPlaying, setNodes, setEdges]);

    const onResetSimulation = useCallback(() => {
        setIsPlaying(false);
        setActiveNodeId(null);
        setStepCount(0);
        setCurrentLabel('');
        trailRef.current = [];
    }, []);

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
        trailRef
    };
}
