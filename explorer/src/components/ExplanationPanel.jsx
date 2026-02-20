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
        <div className="slide-in-right" style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            width: '370px',
            maxHeight: '92vh',
            background: 'rgba(12, 12, 22, 0.95)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            borderRadius: '14px',
            padding: '0',
            color: '#e2e8f0',
            boxShadow: '0 8px 40px rgba(0, 0, 0, 0.5)',
            overflowY: 'auto',
            zIndex: 100,
        }}>
            {/* Header */}
            <div style={{
                padding: '16px 18px 12px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
            }}>
                {/* Type badge */}
                <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 600,
                    color: typeConfig.accent,
                    background: `${typeConfig.accent}18`,
                    padding: '2px 8px',
                    borderRadius: '6px',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                }}>
                    {typeConfig.icon} {typeConfig.label}
                </span>

                <span style={{
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: '#e2e8f0',
                    flex: 1,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                }}>
                    {node.data.label}
                </span>

                <button
                    onClick={onClose}
                    style={{
                        cursor: 'pointer',
                        background: 'rgba(255,255,255,0.05)',
                        border: 'none',
                        color: '#64748b',
                        fontSize: '0.9rem',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        transition: 'all 0.15s',
                    }}
                >
                    ✕
                </button>
            </div>

            {/* Body */}
            <div style={{ padding: '14px 18px' }}>
                {/* Tabs */}
                <div style={{ display: 'flex', gap: '4px', marginBottom: '14px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', padding: '3px' }}>
                    {[
                        { key: 'technical', label: '⚙️ Technical' },
                        { key: 'analogy', label: '🎭 Analogy' },
                    ].map(t => (
                        <button
                            key={t.key}
                            onClick={() => setTab(t.key)}
                            style={{
                                flex: 1,
                                padding: '7px 0',
                                borderRadius: '6px',
                                border: 'none',
                                background: tab === t.key ? 'rgba(255,255,255,0.08)' : 'transparent',
                                color: tab === t.key ? '#e2e8f0' : '#64748b',
                                fontSize: '0.78rem',
                                fontWeight: tab === t.key ? 600 : 400,
                                cursor: 'pointer',
                                transition: 'all 0.15s',
                            }}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                {/* Difficulty */}
                <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
                    {['beginner', 'intermediate', 'advanced'].map((lvl) => (
                        <button
                            key={lvl}
                            onClick={() => setLevel(lvl)}
                            style={{
                                flex: 1,
                                padding: '4px 0',
                                borderRadius: '6px',
                                border: level === lvl ? `1px solid ${typeConfig.accent}44` : '1px solid rgba(255,255,255,0.06)',
                                background: level === lvl ? `${typeConfig.accent}12` : 'transparent',
                                color: level === lvl ? typeConfig.accent : '#64748b',
                                fontSize: '0.7rem',
                                fontWeight: level === lvl ? 600 : 400,
                                cursor: 'pointer',
                                textTransform: 'capitalize',
                                transition: 'all 0.15s',
                            }}
                        >
                            {lvl}
                        </button>
                    ))}
                </div>

                {renderContent()}
            </div>

            {/* Footer */}
            {(node.data.file || node.data.original_data?.file) && (
                <div style={{
                    padding: '10px 18px',
                    borderTop: '1px solid rgba(255,255,255,0.04)',
                    fontSize: '0.7rem',
                    color: '#475569',
                    display: 'flex',
                    gap: '12px',
                }}>
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
