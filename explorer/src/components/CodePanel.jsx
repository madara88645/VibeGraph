import React, { useEffect, useRef, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
    const [codeData, setCodeData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
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
                const response = await fetch('http://localhost:8000/api/snippet', {
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
                setError('Backend bağlantısı kurulamadı');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchCode();
    }, [activeNode, isOpen]);

    // Auto-scroll to highlighted function
    useEffect(() => {
        if (highlightRef.current) {
            highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, [codeData]);

    if (!isOpen) {
        return (
            <button className="code-panel-toggle" onClick={onToggle}>
                <span>{'<>'}</span> Code
            </button>
        );
    }

    const fileName = codeData?.file_path?.split(/[/\\]/).pop() || '';
    const hasFullSource = codeData?.full_source;
    const startLine = codeData?.start_line;
    const endLine = codeData?.end_line;

    return (
        <div className="code-panel">
            {/* Header */}
            <div className="code-panel-header">
                <div className="code-panel-title">
                    <span className="code-icon">{'<>'}</span>
                    <span className="code-file-name">
                        {fileName || 'No file'}
                    </span>
                    {activeNode && (
                        <span className="code-node-name">
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
                <button className="code-panel-close" onClick={onToggle}>✕</button>
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
                            ? '👻 Ghost Runner başlatıldığında kod otomatik gösterilecek...'
                            : 'Bir node\'a tıklayın veya Ghost Runner\'ı başlatın'}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CodePanel;
