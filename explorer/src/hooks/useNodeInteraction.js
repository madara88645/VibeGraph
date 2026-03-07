import { useState, useCallback } from 'react';

export function useNodeInteraction() {
    const [selectedNode, setSelectedNode] = useState(null);
    const [explanation, setExplanation] = useState(null);
    const [loading, setLoading] = useState(false);

    // Code Panel state
    const [codePanelOpen, setCodePanelOpen] = useState(true);
    const [codePanelNode, setCodePanelNode] = useState(null);

    // New component states
    const [chatOpen, setChatOpen] = useState(false);
    const [learningPathOpen, setLearningPathOpen] = useState(false);

    const fetchExplanation = useCallback(async (node, type = 'technical', level = 'intermediate') => {
        setLoading(true);
        try {
            const file_path = node.data.file || node.data.original_data?.file;
            const payload = {
                file_path: file_path || null,
                node_id: node.id,
                type,
                level
            };

            // Ensure we hit the Vite proxy endpoint or use absolute backend address in dev
            // Changing this to a relative path /api/explain as per DevOps plan
            const response = await fetch('/api/explain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            setExplanation(data.explanation ? data : "No explanation returned.");
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
