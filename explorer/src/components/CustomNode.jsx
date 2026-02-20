import React, { memo } from 'react'
import { Handle, Position } from '@xyflow/react'

const TYPE_STYLES = {
  function: { icon: '⚡', color: 'var(--accent-fn)' },
  class:    { icon: '🏗️', color: 'var(--accent-class)' },
  entry:    { icon: '🚀', color: 'var(--accent-entry)' },
}

function CustomNode({ data, selected }) {
  const { icon, color } = TYPE_STYLES[data.nodeType] ?? TYPE_STYLES.function
  const dimmed = data.dimmed === true

  const style = {
    background: 'var(--bg-secondary)',
    border: `1.5px solid ${selected ? '#fff' : color}`,
    borderRadius: '8px',
    padding: '8px 14px',
    minWidth: '140px',
    maxWidth: '200px',
    cursor: 'pointer',
    opacity: dimmed ? 0.35 : 1,
    boxShadow: data.glowing
      ? `0 0 12px 3px ${color}`
      : selected
      ? `0 0 0 2px ${color}44`
      : 'none',
    transition: 'opacity 0.2s, box-shadow 0.2s',
  }

  return (
    <>
      <Handle type="target" position={Position.Left} style={{ background: color }} />
      <div style={style}>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px' }}>
          {icon} {data.nodeType}
        </div>
        <div
          style={{
            fontWeight: 600,
            color,
            fontSize: '13px',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
          title={data.label}
        >
          {data.label}
        </div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: color }} />
    </>
  )
}

export default memo(CustomNode)
