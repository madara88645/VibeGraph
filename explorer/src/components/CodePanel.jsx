import React, { useEffect, useRef, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useToast } from '../hooks/useToast';

/**
 * CodePanel — Bottom panel that shows code for the active node.
 * 
 * Two modes:
 *   1. Ghost Runner active → auto-follows current node's code
 *   2. Manual → shows clicked node's code
 * 
 * Shows the full file with the relevant function highlighted.
 */
const CodePanel = ({ activeNode, isGhostRunning, isOpen, onToggle }) => {
    const addToast = useToast();
    const [codeData, setCodeData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const highlightRef = useRef(null);
    const lastFetchedId = useRef(null);

    // Fetch code when active node changes
    useEffect(() => {
        if (!activeNode || !isOpen) return;
        if (lastFetchedId.current === activeNode.id) return;

        const fetchCode = async () => {
            const filePath = activeNode.data?.file || activeNode.data?.original_data?.file;
            if (!filePath) {
                setCodeData({
                    snippet: `// External: ${activeNode.data?.label || activeNode.id}\n// No source code available`,
                    file_path: null,
                    start_line: null,
                    end_line: null,
                    full_source: null,
                });
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const response = await fetch('/api/snippet', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_path: filePath,
                        node_id: activeNode.id,
                    }),
                });

                if (!response.ok) throw new Error('Failed to fetch');
                const data = await response.json();
                setCodeData(data);
                lastFetchedId.current = activeNode.id;
            } catch (err) {
                setError('Could not connect to backend');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchCode();
    }, [activeNode, isOpen]);

    // Close fullscreen on Escape
    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === 'Escape' && isFullscreen) setIsFullscreen(false);
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [isFullscreen]);

    // Auto-scroll to highlighted function
    useEffect(() => {
        if (highlightRef.current) {
            highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [codeData]);

    if (!isOpen) {
        return (
            <button className="code-panel-toggle" onClick={onToggle} aria-label="Open Code Panel">
                <span aria-hidden="true">{'<>'}</span> Code
            </button>
        );
    }

    const fileName = codeData?.file_path?.split(/[/\\]/).pop() || '';
    const hasFullSource = codeData?.full_source;
    const startLine = codeData?.start_line;
    const endLine = codeData?.end_line;
    const hasCopyText = Boolean(codeData?.full_source || codeData?.snippet);

    return (
        <div className={`code-panel ${isFullscreen ? 'code-panel-fullscreen' : ''}`}>
            {/* Backdrop for fullscreen */}
            {isFullscreen && <div className="code-panel-backdrop" onClick={() => setIsFullscreen(false)} />}

            {/* Header */}
            <div className="code-panel-header">
                <div className="code-panel-title">
                    <span className="code-icon" aria-hidden="true">{'<>'}</span>
                    <span className="code-file-name" title={codeData?.file_path || fileName || 'No file'}>
                        {fileName || 'No file'}
                    </span>
                    {activeNode && (
                        <span className="code-node-name" title={activeNode.data?.label}>
                            → {activeNode.data?.label}
                        </span>
                    )}
                    {startLine && (
                        <span className="code-line-range">
                            L{startLine}–{endLine}
                        </span>
                    )}
                    {isGhostRunning && (
                        <span className="code-follow-badge">
                            👻 Following
                        </span>
                    )}
                </div>
                <div style={{ display: 'flex', gap: '4px' }}>
                    {!hasCopyText && (
                        <span
                            id="copy-btn-hint"
                            style={{
                                position: 'absolute',
                                width: '1px',
                                height: '1px',
                                padding: 0,
                                margin: '-1px',
                                overflow: 'hidden',
                                clip: 'rect(0,0,0,0)',
                                whiteSpace: 'nowrap',
                                borderWidth: 0,
                            }}
                        >
                            Nothing to copy yet
                        </span>
                    )}
                    <span
                        title={hasCopyText ? "Copy code" : "Nothing to copy yet"}
                        style={{ display: 'inline-flex' }}
                    >
                        <button
                            onClick={() => {
                            const text = codeData?.full_source || codeData?.snippet;
                            if (!text) {
                                addToast('Nothing to copy yet', 'error');
                                return;
                            }

                            const fallbackCopyText = (value) => {
                                try {
                                    const textarea = document.createElement('textarea');
                                    textarea.value = value;
                                    textarea.style.position = 'fixed';
                                    textarea.style.top = '0';
                                    textarea.style.left = '0';
                                    textarea.style.opacity = '0';
                                    document.body.appendChild(textarea);
                                    textarea.focus();
                                    textarea.select();
                                    const successful = document.execCommand('copy');
                                    document.body.removeChild(textarea);
                                    return successful;
                                } catch (err) {
                                    console.error('Fallback copy failed', err);
                                    return false;
                                }
                            };

                            const notifyResult = (ok) => {
                                if (ok) {
                                    addToast('Code copied to clipboard!', 'success');
                                } else {
                                    addToast('Failed to copy', 'error');
                                }
                            };

                            try {
                                if (navigator && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
                                    navigator.clipboard.writeText(text).then(
                                        () => addToast('Code copied to clipboard!', 'success'),
                                        () => notifyResult(fallbackCopyText(text))
                                    );
                                } else {
                                    notifyResult(fallbackCopyText(text));
                                }
                            } catch (err) {
                                console.error('Clipboard copy failed', err);
                                notifyResult(fallbackCopyText(text));
                            }
                        }}
                        aria-label="Copy code"
                        aria-describedby={!hasCopyText ? "copy-btn-hint" : undefined}
                        disabled={!hasCopyText}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--text-secondary)',
                            cursor: hasCopyText ? 'pointer' : 'not-allowed',
                            padding: '4px 8px',
                            fontSize: '13px',
                            opacity: hasCopyText ? 1 : 0.5,
                        }}
                    >
                        Copy
                    </button>
                    </span>
                    <button
                        className="code-panel-close"
                        onClick={() => setIsFullscreen(prev => !prev)}
                        title={isFullscreen ? 'Exit fullscreen' : 'Expand code'}
                        aria-label={isFullscreen ? 'Exit fullscreen' : 'Expand code'}
                    >
                        <span aria-hidden="true">{isFullscreen ? '⊙' : '⛶'}</span>
                    </button>
                    <button className="code-panel-close" onClick={() => { setIsFullscreen(false); onToggle(); }} title="Close Code Panel" aria-label="Close Code Panel"><span aria-hidden="true">✕</span></button>
                </div>
            </div>

            {/* Content */}
            <div className="code-panel-content">
                {loading && (
                    <div className="code-loading">
                        <div className="code-spinner" />
                        Loading code...
                    </div>
                )}

                {error && (
                    <div className="code-error">{error}</div>
                )}

                {!loading && !error && codeData && (
                    hasFullSource ? (
                        // Full file view with highlighted section
                        <div className="code-full-file">
                            {codeData.full_source.split('\n').map((line, i) => {
                                const lineNum = i + 1;
                                const isHighlighted = startLine && endLine && lineNum >= startLine && lineNum <= endLine;
                                return (
                                    <div
                                        key={i}
                                        ref={isHighlighted && lineNum === startLine ? highlightRef : null}
                                        className={`code-line ${isHighlighted ? 'code-line-highlight' : ''}`}
                                    >
                                        <span className="code-line-number">{lineNum}</span>
                                        <pre className="code-line-content">{line || ' '}</pre>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        // Snippet-only view
                        <SyntaxHighlighter
                            language="python"
                            style={oneDark}
                            showLineNumbers
                            customStyle={{
                                margin: 0,
                                borderRadius: 0,
                                background: 'transparent',
                                fontSize: '0.8rem',
                            }}
                        >
                            {codeData.snippet || '// No code available'}
                        </SyntaxHighlighter>
                    )
                )}

                {!loading && !error && !codeData && (
                    <div className="code-placeholder">
                        {isGhostRunning
                            ? '👻 Code will appear automatically when Ghost Runner starts...'
                            : 'Click a node or start Ghost Runner'}
                    </div>
                )}
            </div>
        </div>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap CodePanel in React.memo() to prevent parsing/rendering
// syntax highlighting on every tick during rapid simulation state changes.
export default React.memo(CodePanel);
