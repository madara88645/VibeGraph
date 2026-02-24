import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeViewer = ({ code }) => {
    if (!code) return null;

    return (
        <div className="code-viewer">
            <div className="code-viewer-header">
                Source Code Preview
            </div>
            <SyntaxHighlighter
                language="python"
                style={vscDarkPlus}
                customStyle={{ margin: 0, padding: '15px', fontSize: '0.85rem' }}
                showLineNumbers={true}
            >
                {code}
            </SyntaxHighlighter>
        </div>
    );
};

export default CodeViewer;
