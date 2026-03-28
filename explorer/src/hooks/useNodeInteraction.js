import { useState, useCallback, useRef } from 'react';

export function useNodeInteraction() {
    const [selectedNode, setSelectedNode] = useState(null);
    const [explanation, setExplanation] = useState(null);
    const [loading, setLoading] = useState(false);
    const explanationCacheRef = useRef(null);
    if (explanationCacheRef.current === null) {
        try {
            const saved = localStorage.getItem('vg_v1_explanationCache');
            if (saved) {
                explanationCacheRef.current = new Map(JSON.parse(saved));
            } else {
                explanationCacheRef.current = new Map();
            }
        } catch {
            explanationCacheRef.current = new Map();
        }
    }

    // Code Panel state
    const [codePanelOpen, setCodePanelOpen] = useState(true);
    const [codePanelNode, setCodePanelNode] = useState(null);

    // New component states
    const [chatOpen, setChatOpen] = useState(false);
    const [learningPathOpen, setLearningPathOpen] = useState(false);

    const fetchExplanation = useCallback(async (node, type = 'technical', level = 'intermediate') => {
        const cacheKey = `${node.id}__${type}__${level}`;
        const cached = explanationCacheRef.current.get(cacheKey);
        if (cached) {
            setExplanation(cached);
            setLoading(false);
            return;
        }

        setLoading(true);
        try {
            const file_path = node.data.file || node.data.original_data?.file;
            const payload = {
                file_path: file_path || null,
                node_id: node.id,
                type,
                level
            };

            const response = await fetch('/api/explain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            const result = data.explanation ? data : "No explanation returned.";
            explanationCacheRef.current.set(cacheKey, result);
            try {
                localStorage.setItem('vg_v1_explanationCache', JSON.stringify([...explanationCacheRef.current.entries()]));
            } catch {}
            setExplanation(result);
        } catch (err) {
            console.error(err);
            setExplanation("Failed to connect to Vibe Teacher (Backend). Is server.py running?");
        } finally {
            setLoading(false);
        }
    }, []);

    const handleSelectNode = useCallback((node) => {
        setSelectedNode(node);
        setCodePanelNode(node);
    }, []);

    const onNodeClick = useCallback(async (event, node) => {
        handleSelectNode(node);
        setExplanation(null);
        setLoading(true);
        fetchExplanation(node, 'technical', 'intermediate');
    }, [handleSelectNode, fetchExplanation]);

    const resetInteractionState = useCallback(() => {
        setSelectedNode(null);
        setExplanation(null);
        explanationCacheRef.current.clear();
        try { localStorage.removeItem('vg_v1_explanationCache'); } catch {}
    }, []);

    return {
        selectedNode,
        setSelectedNode,
        explanation,
        setExplanation,
        loading,
        setLoading,
        codePanelOpen,
        setCodePanelOpen,
        codePanelNode,
        setCodePanelNode,
        chatOpen,
        setChatOpen,
        learningPathOpen,
        setLearningPathOpen,
        fetchExplanation,
        handleSelectNode,
        onNodeClick,
        resetInteractionState
    };
}
