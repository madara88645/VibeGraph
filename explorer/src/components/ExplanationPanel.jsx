import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import CodeViewer from './CodeViewer';

const typeColors = {
    'function': { accent: '#06b6d4', label: 'Function', icon: '⚡' },
    'class': { accent: '#a855f7', label: 'Class', icon: '🏗️' },
    'entry_point': { accent: '#22c55e', label: 'Entry Point', icon: '🚀' },
    'builtin': { accent: '#3b82f6', label: 'Built-in', icon: '🐍' },
    'external': { accent: '#f97316', label: 'External', icon: '📦' },
    'imported_local': { accent: '#14b8a6', label: 'Imported', icon: '🔗' },
    'module': { accent: '#eab308', label: 'Module', icon: '📁' },
    'unresolved': { accent: '#94a3b8', label: 'Reference', icon: '?' },
    'default': { accent: '#64748b', label: 'Reference', icon: '○' },
};

const ExplanationPanel = ({ node, explanation, loading, onClose, fetchExplanation, onOpenAiSettings }) => {
    const [tab, setTab] = useState('technical');
    const [level, setLevel] = useState('intermediate');
    const [lastNode, setLastNode] = useState(null);
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        if (node) {
            Promise.resolve().then(() => {
                setLastNode(node);
                setIsOpen(true);
            });
            if (fetchExplanation) {
                fetchExplanation(node, tab, level);
            }
        } else {
            Promise.resolve().then(() => {
                setIsOpen(false);
            });
        }
    }, [fetchExplanation, level, node, tab]);

    // Use a secondary state to completely unmount/hide pointer events when animation is finished
    const [isRendered, setIsRendered] = useState(false);

    useEffect(() => {
        if (isOpen) {
            Promise.resolve().then(() => {
                setIsRendered(true);
            });
        } else {
            const timer = setTimeout(() => {
                setIsRendered(false);
            }, 300); // match transition duration
            return () => clearTimeout(timer);
        }
    }, [isOpen]);

    if (!isRendered && !node) return null;

    // Use lastNode if node is null (during animate-out) so content doesn't instantly disappear!
    const activeNode = node || lastNode;
    if (!activeNode) return null;

    const nodeType = activeNode.data.entry_point ? 'entry_point' : (activeNode.data.type || 'default');
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
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>AI is thinking...</span>
                    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </div>
            );
        }

        if (!explanation) {
            return <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '20px 0' }}>Click a node to get an AI explanation.</p>;
        }

        const aiResponse = explanation.explanation || explanation;
        const codeSnippet = explanation.snippet || activeNode.data.snippet;

        // Check for error state!
        const isClientMissingKey = typeof explanation === 'string' && explanation.includes('Open AI Settings');
        const isBackendError = typeof aiResponse === 'object' && aiResponse !== null && (aiResponse.is_error || aiResponse.technical === 'An unexpected error occurred.' || aiResponse.technical === 'OpenRouter API key is required.');

        if (isClientMissingKey || isBackendError) {
            let errorTitle = "Connection Error";
            let errorMsg = "An unexpected error occurred. Please check your connection or OpenRouter status.";
            let errorTakeaway = "Check your OpenRouter status or API key.";
            let errorIcon = "⚠️";
            let showSettingsBtn = false;
            let showRetryBtn = false;

            if (isClientMissingKey) {
                errorTitle = "API Key Missing";
                errorMsg = "You need to add a valid OpenRouter API key to enable AI explanations.";
                errorTakeaway = "Add a valid API key in the AI Settings panel.";
                errorIcon = "🔑";
                showSettingsBtn = true;
            } else {
                const analogy = aiResponse.analogy || "";
                const technical = aiResponse.technical || "";
                const takeaway = aiResponse.key_takeaway || "";

                if (analogy.includes("Key") || analogy.includes("Anahtar") || technical.toLowerCase().includes("key") || technical.toLowerCase().includes("auth")) {
                    errorTitle = "Invalid API Key";
                    errorMsg = technical;
                    errorTakeaway = takeaway;
                    errorIcon = "🔑";
                    showSettingsBtn = true;
                } else if (analogy.includes("Limit") || analogy.includes("Sınır")) {
                    errorTitle = "Rate Limit Exceeded";
                    errorMsg = technical;
                    errorTakeaway = takeaway;
                    errorIcon = "⌛";
                    showRetryBtn = true;
                } else if (analogy.includes("Timeout") || analogy.includes("Zaman Aşımı")) {
                    errorTitle = "Connection Timeout";
                    errorMsg = technical;
                    errorTakeaway = takeaway;
                    errorIcon = "🔌";
                    showRetryBtn = true;
                } else if (analogy.includes("Connection") || analogy.includes("Bağlantı")) {
                    errorTitle = "Connection Failed";
                    errorMsg = technical;
                    errorTakeaway = takeaway;
                    errorIcon = "🌐";
                    showRetryBtn = true;
                } else if (analogy.includes("Request") || analogy.includes("İstek")) {
                    errorTitle = "Bad Request";
                    errorMsg = technical;
                    errorTakeaway = takeaway;
                    errorIcon = "⚙️";
                } else {
                    errorTitle = analogy || "Connection Error";
                    errorMsg = technical || "An unexpected error occurred.";
                    errorTakeaway = takeaway || "Please check your internet connection or OpenRouter status.";
                    errorIcon = "⚠️";
                    showRetryBtn = true;
                }
            }

            return (
                <div className="fade-in" style={{
                    padding: '16px',
                    borderRadius: '12px',
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    borderLeft: '4px solid var(--error-rose, #ef4444)',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
                    backdropFilter: 'blur(8px)',
                    margin: '10px 0'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                        <span style={{ fontSize: '1.5rem' }}>{errorIcon}</span>
                        <h4 style={{ margin: 0, color: '#fca5a5', fontSize: '1rem', fontWeight: '600' }}>{errorTitle}</h4>
                    </div>
                    <div className="markdown-content" style={{ margin: '0 0 12px', fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                        <ReactMarkdown>{errorMsg}</ReactMarkdown>
                    </div>
                    <div style={{
                        background: 'rgba(252, 165, 165, 0.05)',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        fontSize: '0.8rem',
                        color: 'var(--text-muted)',
                        borderLeft: '2px solid rgba(252, 165, 165, 0.3)',
                        marginBottom: '14px'
                    }}>
                        <strong>💡 Suggestion:</strong> {errorTakeaway}
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        {showSettingsBtn && onOpenAiSettings && (
                            <button
                                onClick={() => onOpenAiSettings()}
                                style={{
                                    background: 'var(--accent-primary, #ef4444)',
                                    color: 'white',
                                    border: 'none',
                                    padding: '8px 16px',
                                    borderRadius: '6px',
                                    fontSize: '0.8rem',
                                    fontWeight: '500',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                }}
                                onMouseEnter={(e) => e.target.style.filter = 'brightness(1.1)'}
                                onMouseLeave={(e) => e.target.style.filter = 'none'}
                            >
                                ⚙️ Open AI Settings
                            </button>
                        )}
                        {showRetryBtn && (
                            <button
                                onClick={() => fetchExplanation && fetchExplanation(activeNode, tab, level)}
                                style={{
                                    background: 'rgba(255, 255, 255, 0.08)',
                                    color: 'var(--text-primary)',
                                    border: '1px solid rgba(255, 255, 255, 0.15)',
                                    padding: '8px 16px',
                                    borderRadius: '6px',
                                    fontSize: '0.8rem',
                                    fontWeight: '500',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                }}
                                onMouseEnter={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.12)'}
                                onMouseLeave={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.08)'}
                            >
                                🔄 Retry
                            </button>
                        )}
                    </div>
                </div>
            );
        }

        if (typeof aiResponse === 'object' && aiResponse !== null && aiResponse.technical) {
            return (
                <div
                    className="fade-in"
                    style={{ fontSize: '0.88rem', lineHeight: '1.7', color: 'var(--text-secondary)' }}
                    role="tabpanel"
                    id={`panel-${tab}`}
                    aria-labelledby={`tab-${tab}`}
                >
                    {tab === 'analogy' && (
                        <div>
                            <p style={{ margin: '0 0 12px' }}>{aiResponse.analogy}</p>
                            <div style={{
                                background: `${typeConfig.accent}12`,
                                padding: '10px 12px',
                                borderRadius: '8px',
                                borderLeft: `3px solid ${typeConfig.accent}`,
                                fontSize: '0.82rem',
                            }}>
                                <strong style={{ color: 'var(--text-primary)' }}>💡 Takeaway:</strong> {aiResponse.key_takeaway}
                            </div>
                        </div>
                    )}

                    {tab === 'technical' && (
                        <div>
                            <div className="markdown-content">
                                <ReactMarkdown>{aiResponse.technical}</ReactMarkdown>
                            </div>
                            <div style={{
                                background: `${typeConfig.accent}12`,
                                padding: '10px 12px',
                                borderRadius: '8px',
                                borderLeft: `3px solid ${typeConfig.accent}`,
                                fontSize: '0.82rem',
                                marginTop: '12px',
                             }}>
                                <strong style={{ color: 'var(--text-primary)' }}>💡 Takeaway:</strong> {aiResponse.key_takeaway}
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
            <div className="fade-in" style={{ fontSize: '0.88rem', lineHeight: '1.7', color: 'var(--text-secondary)' }}>
                <ReactMarkdown>{typeof aiResponse === 'string' ? aiResponse : JSON.stringify(aiResponse)}</ReactMarkdown>
                {codeSnippet && <CodeViewer code={codeSnippet} />}
            </div>
        );
    };

    return (
        <div className={`explanation-panel ${isOpen ? 'open' : ''}`}>
            {/* Header */}
            <div className="ep-header">
                {/* Type badge */}
                <span className="ep-type" style={{ color: typeConfig.accent, background: `${typeConfig.accent}18`, borderColor: `${typeConfig.accent}40` }}>
                    {typeConfig.icon} {typeConfig.label}
                </span>

                <span className="ep-title" title={activeNode.data.label}>
                    {activeNode.data.label}
                </span>

                <button
                    onClick={onClose}
                    className="ep-close"
                    title="Close Explanation Panel"
                    aria-label="Close Explanation Panel"
                >
                    <span aria-hidden="true">✕</span>
                </button>
            </div>

            {/* Body */}
            <div className="ep-body">
                {/* Tabs */}
                <div className="ep-tabs" role="tablist" aria-label="Explanation modes">
                    {[
                        { key: 'technical', icon: '⚙️', label: 'Technical' },
                        { key: 'analogy', icon: '🎭', label: 'Analogy' },
                    ].map(t => (
                        <button
                            key={t.key}
                            id={`tab-${t.key}`}
                            role="tab"
                            aria-selected={tab === t.key}
                            aria-controls={`panel-${t.key}`}
                            onClick={() => setTab(t.key)}
                            className={`ep-tab ${tab === t.key ? 'active' : ''}`}
                            aria-label={`Switch to ${t.label} tab`}
                        >
                            <span aria-hidden="true">{t.icon}</span> {t.label}
                        </button>
                    ))}
                </div>

                {/* Difficulty */}
                <div className="ep-levels" role="group" aria-label="Difficulty level">
                    {['beginner', 'intermediate', 'advanced'].map((lvl) => (
                        <button
                            key={lvl}
                            onClick={() => setLevel(lvl)}
                            aria-pressed={level === lvl}
                            className={`ep-level ${level === lvl ? 'active' : ''}`}
                            aria-label={`Set difficulty level to ${lvl}`}
                            style={level === lvl ? { borderColor: `${typeConfig.accent}44`, background: `${typeConfig.accent}12`, color: typeConfig.accent } : undefined}
                        >
                            {lvl}
                        </button>
                    ))}
                </div>

                {renderContent()}
            </div>

            {/* Footer */}
            {(activeNode.data.file || activeNode.data.original_data?.file) && (
                <div className="ep-footer">
                    <span title={activeNode.data.file || activeNode.data.original_data?.file}><span aria-hidden="true">📄</span> {activeNode.data.file || activeNode.data.original_data?.file}</span>
                    {(activeNode.data.lineno || activeNode.data.original_data?.lineno) && (
                        <span>L{activeNode.data.lineno || activeNode.data.original_data?.lineno}</span>
                    )}
                </div>
            )}
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap ExplanationPanel in React.memo() to prevent parsing/rendering
// Markdown on every tick during rapid simulation state changes.
export default React.memo(ExplanationPanel);
