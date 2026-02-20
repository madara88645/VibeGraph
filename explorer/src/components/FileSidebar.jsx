import React, { useMemo } from 'react'

export default function FileSidebar({ nodes, activeFile, onFileSelect }) {
  const files = useMemo(() => {
    const set = new Set(nodes.map((n) => n.data.file))
    return ['(all files)', ...Array.from(set).sort()]
  }, [nodes])

  return (
    <aside
      style={{
        width: 'var(--sidebar-width)',
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        flexShrink: 0,
      }}
    >
      <div
        style={{
          padding: '10px 12px',
          fontWeight: 700,
          fontSize: '11px',
          letterSpacing: '0.08em',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          borderBottom: '1px solid var(--border)',
        }}
      >
        Files
      </div>

      {files.map((file) => {
        const isActive =
          file === '(all files)' ? activeFile === null : activeFile === file
        return (
          <button
            key={file}
            onClick={() => onFileSelect(file === '(all files)' ? null : file)}
            style={{
              background: isActive ? 'var(--bg-tertiary)' : 'transparent',
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderLeft: isActive
                ? '2px solid var(--accent-fn)'
                : '2px solid transparent',
              borderTop: 'none',
              borderRight: 'none',
              borderBottom: 'none',
              borderRadius: 0,
              padding: '7px 12px',
              textAlign: 'left',
              fontSize: '12px',
              width: '100%',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
            title={file}
          >
            {file === '(all files)' ? '📂 All Files' : `📄 ${file}`}
          </button>
        )
      })}
    </aside>
  )
}
