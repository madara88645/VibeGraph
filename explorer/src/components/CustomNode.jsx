import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

import { getShortName } from '../utils/stringUtils';
import { IconFile, NodeTypeIcon } from './icons';

// Accents are theme tokens (index.css → --node-*), so the light theme gets
// deeper hues without a second map here.
const typeConfig = {
    'function': { accent: 'var(--node-fn)', label: 'fn' },
    'class': { accent: 'var(--node-class)', label: 'cls' },
    'entry_point': { accent: 'var(--node-entry)', label: 'entry' },
    'builtin': { accent: 'var(--node-builtin)', label: 'builtin' },
    'external': { accent: 'var(--node-external)', label: 'ext' },
    'imported_local': { accent: 'var(--node-import)', label: 'import' },
    'module': { accent: 'var(--node-module)', label: 'mod' },
    'unresolved': { accent: 'var(--node-ref)', label: 'ref' },
    'default': { accent: 'var(--node-ref)', label: 'ref' },
};

const CustomNode = ({ data, selected }) => {
    const nodeType = data.entry_point ? 'entry_point' : (data.type || 'default');
    const config = typeConfig[nodeType] || typeConfig['default'];

    // Extract short filename
    const fileName = data.file ? getShortName(data.file) : null;

    // Language-aware logic. Defaults are Python (PY); JS/TS override below.
    const lang = data.language || 'python';
    let langPill = 'PY';
    // Built-ins are language-owned, so tint their icon with the language colour
    // instead of the node-type accent to keep the JS/TS distinction visible.
    let iconColor = config.accent;

    if (lang === 'javascript') {
        langPill = 'JS';
        if (nodeType === 'builtin') iconColor = 'var(--node-module)';
    } else if (lang === 'typescript') {
        langPill = 'TS';
        if (nodeType === 'builtin') iconColor = 'var(--node-fn)';
    }

    return (
        <div
            className={`vg-node ${selected ? 'vg-node-selected' : ''}`}
            style={{ '--node-accent': config.accent }}
        >
            <Handle type="target" position={Position.Top} />

            <div className="vg-node-head">
                <NodeTypeIcon type={nodeType} size={14} className="vg-node-icon" style={{ color: iconColor }} />
                <span className="vg-node-label" title={data.label} style={{ color: 'var(--text-primary)' }}>
                    {data.label}
                </span>
            </div>

            <div className="vg-node-meta">
                {fileName && (
                    <span className="vg-node-file" title={fileName} style={{ color: 'var(--text-secondary)' }}>
                        <IconFile size={11} /> {fileName}
                    </span>
                )}
                {data.lineno && (
                    <span className="vg-node-line" style={{ color: 'var(--text-muted)' }}>
                        L{data.lineno}
                    </span>
                )}
                <span className="vg-node-tags">
                    <span className="vg-node-lang">{langPill}</span>
                    <span className="vg-node-type">{config.label}</span>
                </span>
            </div>

            <Handle type="source" position={Position.Bottom} />
        </div>
    );
};

export default memo(CustomNode);
