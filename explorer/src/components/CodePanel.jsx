import React, { useEffect, useRef, useState, useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useToast } from '../hooks/useToast';
import { fetchWithTimeout, getFriendlyAiErrorMessage } from '../utils/aiClient';
import { buildNodeCodeContext } from '../utils/nodeMetadata';
import { getShortName } from '../utils/stringUtils';

const CODE_FETCH_TIMEOUT_MS = 15000;

async function readSnippetError(response) {
    if (response.status === 429) {
        return 'Too many code requests. Slow down and try again.';
    }

    let detail = `Code request failed (${response.status})`;
    try {
        const payload = await response.json();
        detail = payload.detail || payload.message || payload.error || detail;
    } catch {
        // Keep HTTP fallback when the backend response is not JSON.
    }
    return detail;
}

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
        if (!activeNode) {
            setCodeData(null);
            setError(null);
            lastFetchedId.current = null;
            return;
        }
        if (!isOpen) return;
        if (lastFetchedId.current === activeNode.id) return;

        const fetchCode = async () => {
            const nodeContext = buildNodeCodeContext(activeNode);
            const filePath = nodeContext.file_path;
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
                const response = await fetchWithTimeout('/api/snippet', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ...nodeContext,
                        file_path: filePath,
                        node_id: activeNode.id,
                    }),
                }, CODE_FETCH_TIMEOUT_MS);

                if (!response.ok) throw new Error(await readSnippetError(response));
                const data = await response.json();
                setCodeData(data);
                lastFetchedId.current = activeNode.id;
            } catch (err) {
                setError(getFriendlyAiErrorMessage(err, 'Could not connect to backend'));
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

    const fileName = getShortName(codeData?.file_path) || '';
    const hasFullSource = codeData?.full_source;
    const startLine = codeData?.start_line;
    const endLine = codeData?.end_line;
    const hasCopyText = Boolean(codeData?.full_source || codeData?.snippet);

    const isExternalOrBuiltin = codeData?.snippet && (
        codeData.snippet.includes('External or Built-in') || 
        codeData.snippet.includes('External:') || 
        codeData.snippet.includes('(External/Built-in)')
    );

    const isMissingOrInaccessible = codeData?.snippet && (
        codeData.snippet.includes('not found in') || 
        codeData.snippet.includes('Error reading file') ||
        codeData.snippet.includes('Access denied')
    );

    // PERFORMANCE OPTIMIZATION (Bolt): Memoize the result of splitting the full source
    // code into lines to avoid severe garbage collection pressure and CPU overhead
    // during high-frequency render cycles or panel toggles.
    const codeLines = useMemo(() => {
        return codeData?.full_source ? codeData.full_source.split('\n') : [];
    }, [codeData?.full_source]);

    return (
        <>
            <button 
                className={`code-panel-toggle ${isOpen ? 'hidden' : ''}`} 
                onClick={onToggle} 
                title="Open Code Panel" 
                aria-label="Open Code Panel"
            >
                <span aria-hidden="true">{'<>'}</span> Code
            </button>

            <div className={`code-panel ${isOpen ? 'open' : ''} ${isFullscreen ? 'code-panel-fullscreen' : ''}`}>
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
                            <span aria-hidden="true">👻</span> Following
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
                        aria-label={hasCopyText ? "Copy code" : "Nothing to copy yet"}
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
                        title={isFullscreen ? 'Exit fullscreen (Press Esc)' : 'Expand code'}
                        aria-label={isFullscreen ? 'Exit fullscreen (Press Esc)' : 'Expand code'}
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
                            {codeLines.map((line, i) => {
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
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', padding: '16px 20px' }}>
                            {isExternalOrBuiltin && (
                                <div className="fade-in" style={{
                                    padding: '14px 16px',
                                    borderRadius: '10px',
                                    background: 'rgba(59, 130, 246, 0.06)',
                                    border: '1px solid rgba(59, 130, 246, 0.15)',
                                    borderLeft: '4px solid #3b82f6',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '6px',
                                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span style={{ fontSize: '1.2rem' }} aria-hidden="true">📦</span>
                                        <h4 style={{ margin: 0, color: '#93c5fd', fontSize: '0.9rem', fontWeight: '600' }}>External or Built-in Module</h4>
                                    </div>
                                    <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.45' }}>
                                        This code node belongs to an external library or a built-in Python module outside your project, so local source code is not available. AI explanation will be provided based on name and context.
                                    </p>
                                </div>
                            )}

                            {isMissingOrInaccessible && (
                                <div className="fade-in" style={{
                                    padding: '14px 16px',
                                    borderRadius: '10px',
                                    background: 'rgba(234, 179, 8, 0.06)',
                                    border: '1px solid rgba(234, 179, 8, 0.15)',
                                    borderLeft: '4px solid #eab308',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '6px',
                                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span style={{ fontSize: '1.2rem' }} aria-hidden="true">🔍</span>
                                        <h4 style={{ margin: 0, color: '#fef08a', fontSize: '0.9rem', fontWeight: '600' }}>Source File Not Found</h4>
                                    </div>
                                    <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: '1.45' }}>
                                        The local source file for this function could not be found or is inaccessible (possibly a temporary path from a demo or a deleted file). AI explanation will be provided based on the available context.
                                    </p>
                                </div>
                            )}

                            <SyntaxHighlighter
                                language={codeData.language || 'python'}
                                style={oneDark}
                                showLineNumbers
                                customStyle={{
                                    margin: 0,
                                    borderRadius: '8px',
                                    background: 'rgba(0, 0, 0, 0.25)',
                                    fontSize: '0.8rem',
                                    border: '1px solid rgba(255, 255, 255, 0.04)',
                                    padding: '12px',
                                }}
                            >
                                {codeData.snippet || '// No code available'}
                            </SyntaxHighlighter>
                        </div>
                    )
                )}

                {!loading && !error && !codeData && (
                    <div className="code-placeholder">
                        {isGhostRunning
                            ? <><span aria-hidden="true">👻</span> Code will appear automatically when Ghost Runner starts...</>
                            : 'Click a node or start Ghost Runner'}
                    </div>
                )}
            </div>
        </div>
        </>
    );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap CodePanel in React.memo() to prevent parsing/rendering
// syntax highlighting on every tick during rapid simulation state changes.
export default React.memo(CodePanel);
