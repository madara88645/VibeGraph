import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import CodeViewer from './CodeViewer';

const typeColors = {
    'function': { accent: '#06b6d4', label: 'Function', icon: '⚡' },
    'class': { accent: '#a855f7', label: 'Class', icon: '🏗️' },
    'entry_point': { accent: '#22c55e', label: 'Entry Point', icon: '🚀' },
    'default': { accent: '#64748b', label: 'Reference', icon: '○' },
};

const ExplanationPanel = ({ node, explanation, loading, onClose, fetchExplanation }) => {
    const [tab, setTab] = useState('technical');
    const [level, setLevel] = useState('intermediate');

    useEffect(() => {
        if (node && fetchExplanation) {
            fetchExplanation(node, tab, level);
        }
    }, [tab, level, node]);

    if (!node) return null;

    const nodeType = node.data.entry_point ? 'entry_point' : (node.data.type || 'default');
    const typeConfig = typeColors[nodeType] || typeColors['default'];

    const renderContent = () => {
        if (loading) {
            return (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '30px 0', gap: '12px' }}>
                    <div style={{
                        width: '24px', height: '24px',
                        border: `2px solid ${typeConfig.accent}33`,
                        borderTopColor: typeConfig.accent,
                        borderRadius: '50%',
                        animation: 'spin 0.8s linear infinite'
                    }} />
                    <span style={{ color: '#64748b', fontSize: '0.8rem' }}>AI is thinking...</span>
                    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </div>
            );
        }

        if (!explanation) {
            return <p style={{ color: '#64748b', fontSize: '0.85rem', textAlign: 'center', padding: '20px 0' }}>Click a node to get an AI explanation.</p>;
        }

        const aiResponse = explanation.explanation || explanation;
        const codeSnippet = explanation.snippet || node.data.snippet;

        if (typeof aiResponse === 'object' && aiResponse !== null && aiResponse.technical) {
            return (
                <div className="fade-in" style={{ fontSize: '0.88rem', lineHeight: '1.7', color: '#cbd5e1' }}>
                    {tab === 'analogy' && (
                        <div>
                            <p style={{ margin: '0 0 12px' }}>{aiResponse.analogy}</p>
                            <div style={{
                                background: 'rgba(219, 39, 119, 0.08)',
                                padding: '10px 12px',
                                borderRadius: '8px',
                                borderLeft: '3px solid #db2777',
                                fontSize: '0.82rem',
                            }}>
                                <strong style={{ color: '#e2e8f0' }}>💡 Takeaway:</strong> {aiResponse.key_takeaway}
                            </div>
                        </div>
                    )}

                    {tab === 'technical' && (
                        <div>
                            <div className="markdown-content">
                                <ReactMarkdown>{aiResponse.technical}</ReactMarkdown>
                            </div>
                            <div style={{
                                background: 'rgba(59, 130, 246, 0.08)',
                                padding: '10px 12px',
                                borderRadius: '8px',
                                borderLeft: `3px solid ${typeConfig.accent}`,
                                fontSize: '0.82rem',
                                marginTop: '12px',
                            }}>
                                <strong style={{ color: '#e2e8f0' }}>💡 Takeaway:</strong> {aiResponse.key_takeaway}
                            </div>
                            {codeSnippet && (
                                <div style={{ marginTop: '12px' }}>
                                    <CodeViewer code={codeSnippet} />
                                </div>
                            )}
                        </div>
                    )}
                </div>
            );
        }

        // Fallback for string
        return (
            <div className="fade-in" style={{ fontSize: '0.88rem', lineHeight: '1.7', color: '#cbd5e1' }}>
                <ReactMarkdown>{typeof aiResponse === 'string' ? aiResponse : JSON.stringify(aiResponse)}</ReactMarkdown>
                {codeSnippet && <CodeViewer code={codeSnippet} />}
            </div>
        );
    };

    return (
        <div className="slide-in-right explanation-panel">
            {/* Header */}
            <div className="ep-header">
                {/* Type badge */}
                <span className="ep-type" style={{ color: typeConfig.accent, background: `${typeConfig.accent}18`, borderColor: `${typeConfig.accent}40` }}>
                    {typeConfig.icon} {typeConfig.label}
                </span>

                <span className="ep-title">
                    {node.data.label}
                </span>

                <button
                    onClick={onClose}
                    className="ep-close"
                >
                    ✕
                </button>
            </div>

            {/* Body */}
            <div className="ep-body">
                {/* Tabs */}
                <div className="ep-tabs">
                    {[
                        { key: 'technical', label: '⚙️ Technical' },
                        { key: 'analogy', label: '🎭 Analogy' },
                    ].map(t => (
                        <button
                            key={t.key}
                            onClick={() => setTab(t.key)}
                            className={`ep-tab ${tab === t.key ? 'active' : ''}`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                {/* Difficulty */}
                <div className="ep-levels">
                    {['beginner', 'intermediate', 'advanced'].map((lvl) => (
                        <button
                            key={lvl}
                            onClick={() => setLevel(lvl)}
                            className={`ep-level ${level === lvl ? 'active' : ''}`}
                            style={level === lvl ? { borderColor: `${typeConfig.accent}44`, background: `${typeConfig.accent}12`, color: typeConfig.accent } : undefined}
                        >
                            {lvl}
                        </button>
                    ))}
                </div>

                {renderContent()}
            </div>

            {/* Footer */}
            {(node.data.file || node.data.original_data?.file) && (
                <div className="ep-footer">
                    <span>📄 {node.data.file || node.data.original_data?.file}</span>
                    {(node.data.lineno || node.data.original_data?.lineno) && (
                        <span>L{node.data.lineno || node.data.original_data?.lineno}</span>
                    )}
                </div>
            )}
        </div>
    );
};

export default ExplanationPanel;
