import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const CodeViewer = ({ code }) => {
    if (!code) return null;

    return (
        <div style={{
            marginTop: '15px',
            borderRadius: '8px',
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.1)'
        }}>
            <div style={{
                background: '#1e1e1e',
                padding: '5px 10px',
                fontSize: '0.8rem',
                color: '#888',
                borderBottom: '1px solid #333'
            }}>
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
