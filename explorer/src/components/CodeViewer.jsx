import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeViewer = ({ code }) => {
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === 'Escape' && isFullscreen) setIsFullscreen(false);
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [isFullscreen]);

    if (!code) return null;

    const codeBlock = (
        <SyntaxHighlighter
            language="python"
            style={vscDarkPlus}
            customStyle={{ margin: 0, padding: '15px', fontSize: isFullscreen ? '0.9rem' : '0.85rem' }}
            showLineNumbers={true}
        >
            {code}
        </SyntaxHighlighter>
    );

    return (
        <>
            {/* Inline compact preview */}
            <div className="code-viewer">
                <div className="code-viewer-header">
                    <span>Source Code Preview</span>
                    <button
                        className="code-viewer-expand"
                        onClick={() => setIsFullscreen(true)}
                        title="Expand code"
                        aria-label="Expand code"
                    >
                        <span aria-hidden="true">⛶</span>
                    </button>
                </div>
                {codeBlock}
            </div>

            {/* Fullscreen overlay via portal */}
            {isFullscreen && ReactDOM.createPortal(
                <div className="code-viewer-overlay" onClick={() => setIsFullscreen(false)}>
                    <div className="code-viewer-fullscreen" onClick={(e) => e.stopPropagation()}>
                        <div className="code-viewer-header">
                            <span>Source Code Preview</span>
                            <button
                                className="code-viewer-expand"
                                onClick={() => setIsFullscreen(false)}
                                title="Exit fullscreen"
                                aria-label="Exit fullscreen"
                            >
                                <span aria-hidden="true">✕</span>
                            </button>
                        </div>
                        {codeBlock}
                    </div>
                </div>,
                document.body
            )}
        </>
    );
};

export default CodeViewer;
