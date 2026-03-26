import React, { useState, useCallback, useEffect } from 'react';
import { useReactFlow } from 'reactflow';

const LearningPath = ({ selectedFile, allNodes, onSelectNode, onSelectFile, isOpen, onToggle }) => {
    const [steps, setSteps] = useState([]);
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { fitView } = useReactFlow();

    // Fetch learning path when opened or file changes
    useEffect(() => {
        if (!isOpen || !selectedFile) return;

        const fetchPath = async () => {
            setLoading(true);
            setError(null);
            setSteps([]);
            setCurrentStep(0);

            try {
                const response = await fetch('/api/learning-path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: selectedFile }),
                });

                if (!response.ok) throw new Error(`Server responded ${response.status}`);
                const data = await response.json();

                if (data.steps && data.steps.length > 0) {
                    setSteps(data.steps);
                } else {
                    setError('No steps found.');
                }
            } catch (err) {
                setError(`Error: ${err.message}`);
            } finally {
                setLoading(false);
            }
        };

        fetchPath();
    }, [isOpen, selectedFile]);

    const goToStep = useCallback((idx) => {
        if (idx < 0 || idx >= steps.length) return;
        setCurrentStep(idx);

        const step = steps[idx];
        if (!step) return;

        // Find the node in allNodes
        const node = allNodes.find(
            (n) => n.id === step.node_id || n.data?.label === step.node_name
        );

        if (node) {
            if (node.data?.file) onSelectFile(node.data.file);
            onSelectNode(node);

            // Use fitView with a small timeout to ensure layout/selection is finished
            setTimeout(() => {
                fitView({
                    nodes: [node],
                    duration: 800,
                    padding: 2.0, // Large padding to keep context but center node
                });
            }, 50);
        }
    }, [steps, allNodes, onSelectFile, onSelectNode, fitView]);

    if (!isOpen) return null;

    const progress = steps.length > 0 ? ((currentStep + 1) / steps.length) * 100 : 0;

    return (
        <div className="lp-bar">
            {/* Header / Icon */}
            <div className="lp-bar-icon">🎯</div>

            {/* Navigation & Info */}
            <div className="lp-bar-main">
                <button
                    className="lp-bar-nav"
                    onClick={() => goToStep(currentStep - 1)}
                    disabled={currentStep === 0 || loading}
                    title={loading ? "Analyzing File..." : currentStep === 0 ? "Already at first step" : "Previous Step"}
                    aria-label="Previous Step"
                >
                    ←
                </button>

                <div className="lp-bar-info">
                    {loading ? (
                        <span className="lp-bar-loading">Analyzing File...</span>
                    ) : error ? (
                        <span className="lp-bar-error">{error}</span>
                    ) : steps.length > 0 ? (
                        <>
                            <span className="lp-bar-step">Step {currentStep + 1}/{steps.length}:</span>
                            <span className="lp-bar-node">{steps[currentStep].node_name || steps[currentStep].node_id}</span>
                        </>
                    ) : (
                        <span className="lp-bar-empty">No steps</span>
                    )}
                </div>

                <button
                    className="lp-bar-nav"
                    onClick={() => goToStep(currentStep + 1)}
                    disabled={currentStep === steps.length - 1 || loading}
                    title={loading ? "Analyzing File..." : currentStep === steps.length - 1 ? "Already at last step" : "Next Step"}
                    aria-label="Next Step"
                >
                    →
                </button>
            </div>

            {/* Close */}
            <button className="lp-bar-close" onClick={onToggle} title="Close Learning Path" aria-label="Close Learning Path">✕</button>

            {/* Tiny Progress line at the very bottom */}
            {steps.length > 0 && (
                <div className="lp-bar-progress">
                    <div className="lp-bar-progress-fill" style={{ width: `${progress}%` }} />
                </div>
            )}
        </div>
    );
};

export default LearningPath;
