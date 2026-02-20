import React from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

export default function CodePanel({ activeNode }) {
  if (!activeNode) {
    return (
      <div
        style={{
          height: 'var(--panel-height)',
          background: 'var(--bg-secondary)',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          fontSize: '13px',
        }}
      >
        Click a node to view its source code
      </div>
    )
  }

  const { label, file, lineno, source } = activeNode.data

  return (
    <div
      style={{
        height: 'var(--panel-height)',
        background: 'var(--bg-secondary)',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '6px 14px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 700, color: 'var(--accent-fn)' }}>{label}</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
          {file} : line {lineno}
        </span>
      </div>

      {/* Code */}
      <div style={{ overflowY: 'auto', flex: 1 }}>
        <SyntaxHighlighter
          language="python"
          style={vscDarkPlus}
          customStyle={{ margin: 0, padding: '10px 14px', fontSize: '12px', background: 'transparent' }}
          showLineNumbers
          startingLineNumber={lineno}
          wrapLines
        >
          {source || '# No source available'}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}
