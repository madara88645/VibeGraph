import React, { useState, useCallback, useEffect } from 'react';
import { useReactFlow } from 'reactflow';

const LearningPath = ({ selectedFile, allNodes, onSelectNode, onSelectFile, isOpen, onToggle }) => {
    const [steps, setSteps] = useState([]);
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { setCenter } = useReactFlow();

    // Fetch learning path when opened or file changes
    useEffect(() => {
        if (!isOpen || !selectedFile) return;

        const fetchPath = async () => {
            setLoading(true);
            setError(null);
            setSteps([]);
            setCurrentStep(0);

            try {
                const response = await fetch('http://localhost:8000/api/learning-path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ file_path: selectedFile }),
                });

                if (!response.ok) throw new Error(`Server responded ${response.status}`);
                const data = await response.json();

                if (data.steps && data.steps.length > 0) {
                    setSteps(data.steps);
                } else {
                    setError('No learning steps returned for this file.');
                }
            } catch (err) {
                setError(`Failed to load: ${err.message}`);
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
            if (node.position) {
                setCenter(node.position.x + 86, node.position.y + 18, { zoom: 1.5, duration: 600 });
            }
        }
    }, [steps, allNodes, onSelectFile, onSelectNode, setCenter]);

    if (!isOpen) return null;

    const progress = steps.length > 0 ? ((currentStep + 1) / steps.length) * 100 : 0;

    return (
        <div className="learning-path-overlay" onClick={onToggle}>
            <div className="learning-path" onClick={(e) => e.stopPropagation()}>
                {/* Header */}
                <div className="lp-header">
                    <div className="lp-header-left">
                        <span>🎯</span>
                        <h2>Learning Path</h2>
                    </div>
                    {selectedFile && (
                        <span className="lp-file-name">{selectedFile.split(/[/\\]/).pop()}</span>
                    )}
                    <button className="lp-close" onClick={onToggle}>✕</button>
                </div>

                {/* Progress bar */}
                {steps.length > 0 && (
                    <div className="lp-progress-container">
                        <div className="lp-progress-bar">
                            <div className="lp-progress-fill" style={{ width: `${progress}%` }} />
                        </div>
                        <span className="lp-progress-text">Step {currentStep + 1} / {steps.length}</span>
                    </div>
                )}

                {/* Content */}
                <div className="lp-content">
                    {loading && (
                        <div className="lp-loading">
                            <div className="code-spinner" />
                            <span>Generating learning path…</span>
                        </div>
                    )}

                    {error && (
                        <div className="lp-error">{error}</div>
                    )}

                    {!loading && !error && steps.length > 0 && (
                        <div className="lp-steps">
                            {steps.map((step, idx) => (
                                <button
                                    key={idx}
                                    className={`lp-step ${idx === currentStep ? 'active' : ''} ${idx < currentStep ? 'completed' : ''}`}
                                    onClick={() => goToStep(idx)}
                                >
                                    <div className="lp-step-number">
                                        {idx < currentStep ? '✓' : idx + 1}
                                    </div>
                                    <div className="lp-step-info">
                                        <span className="lp-step-name">{step.node_name || step.node_id}</span>
                                        {step.reason && (
                                            <span className="lp-step-reason">{step.reason}</span>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Navigation */}
                {steps.length > 0 && (
                    <div className="lp-nav">
                        <button
                            className="lp-nav-btn"
                            onClick={() => goToStep(currentStep - 1)}
                            disabled={currentStep === 0}
                        >
                            ← Previous
                        </button>
                        <button
                            className="lp-nav-btn lp-nav-next"
                            onClick={() => goToStep(currentStep + 1)}
                            disabled={currentStep === steps.length - 1}
                        >
                            Next →
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default LearningPath;
