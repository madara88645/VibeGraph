import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

import { getShortName } from '../utils/stringUtils';

const typeConfig = {
    'function': { icon: '⚡', accent: '#06b6d4', bg: 'rgba(6, 182, 212, 0.08)', label: 'fn' },
    'class': { icon: '🏗️', accent: '#a855f7', bg: 'rgba(168, 85, 247, 0.08)', label: 'cls' },
    'entry_point': { icon: '🚀', accent: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', label: 'entry' },
    'builtin': { icon: '🐍', accent: '#3b82f6', bg: 'rgba(59, 130, 246, 0.08)', label: 'builtin' },
    'external': { icon: '📦', accent: '#f97316', bg: 'rgba(249, 115, 22, 0.08)', label: 'ext' },
    'imported_local': { icon: '🔗', accent: '#14b8a6', bg: 'rgba(20, 184, 166, 0.08)', label: 'import' },
    'module': { icon: '📁', accent: '#eab308', bg: 'rgba(234, 179, 8, 0.10)', label: 'mod' },
    'unresolved': { icon: '?', accent: '#94a3b8', bg: 'rgba(148, 163, 184, 0.08)', label: 'ref' },
    'default': { icon: '○', accent: '#64748b', bg: 'rgba(100, 116, 139, 0.06)', label: 'ref' },
};

const CustomNode = ({ data, selected }) => {
    const nodeType = data.entry_point ? 'entry_point' : (data.type || 'default');
    const config = typeConfig[nodeType] || typeConfig['default'];

    // Extract short filename
    const fileName = data.file ? getShortName(data.file) : null;

    return (
        <div
            className={`vg-node ${selected ? 'vg-node-selected' : ''}`}
            style={{
                '--node-accent': config.accent,
                '--node-bg': config.bg,
            }}
        >
            <Handle
                type="target"
                position={Position.Top}
                style={{ background: config.accent, width: 6, height: 6, border: 'none' }}
            />

            {/* Header Row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{ fontSize: '0.85rem' }}>{config.icon}</span>
                <span
                    title={data.label}
                    style={{
                        fontSize: '0.82rem',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        flex: 1,
                    }}
                >
                    {data.label}
                </span>
                {/* Type badge */}
                <span
                    style={{
                        fontSize: '0.6rem',
                        fontWeight: 500,
                        color: config.accent,
                        background: `${config.accent}22`,
                        padding: '1px 5px',
                        borderRadius: '4px',
                        letterSpacing: '0.02em',
                        textTransform: 'uppercase',
                    }}
                >
                    {config.label}
                </span>
            </div>

            {/* Meta Row */}
            {(fileName || data.lineno) && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                    {fileName && (
                        <span title={fileName} style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            📄 {fileName}
                        </span>
                    )}
                    {data.lineno && (
                        <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                            L{data.lineno}
                        </span>
                    )}
                </div>
            )}

            <Handle
                type="source"
                position={Position.Bottom}
                style={{ background: config.accent, width: 6, height: 6, border: 'none' }}
            />
        </div>
    );
};

export default memo(CustomNode);
