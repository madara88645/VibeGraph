import React, { useRef } from 'react';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
} from 'reactflow';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';
import { exportAsPng, exportAsSvg } from '../utils/exportGraph';
import { useToast } from '../hooks/useToast';

// Register custom node types
const nodeTypes = {
    custom: CustomNode,
};

// Minimap color based on node type
const minimapNodeColor = (node) => {
    if (node.data?.entry_point) return '#22c55e';
    switch (node.data?.type) {
        case 'function': return '#06b6d4';
        case 'class': return '#a855f7';
        default: return '#334155';
    }
};

const defaultEdgeOptions = {
    type: 'default',
    style: { strokeWidth: 2, stroke: 'rgba(148, 163, 184, 0.4)' },
};

const exportBtnStyle = {
    background: 'var(--color-surface-2)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-primary)',
    padding: '6px 12px',
    cursor: 'pointer',
    fontSize: '12px',
};

const GraphViewer = ({ nodes, edges, onNodesChange, onEdgesChange, onNodeClick }) => {
    const graphRef = useRef(null);
    const addToast = useToast();

    return (
        <div className="graph-canvas">
            <div ref={graphRef} style={{ width: '100%', height: '100%' }}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onNodeClick={onNodeClick}
                    nodeTypes={nodeTypes}
                    defaultEdgeOptions={defaultEdgeOptions}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                    minZoom={0.3}
                    maxZoom={2}
                    proOptions={{ hideAttribution: true }}
                >
                    <MiniMap
                        nodeColor={minimapNodeColor}
                        maskColor="rgba(0, 0, 0, 0.76)"
                        style={{ borderRadius: '12px' }}
                    />
                    <Controls />
                    <Background variant="dots" color="rgba(125, 211, 252, 0.12)" gap={24} size={1} />
                </ReactFlow>
            </div>
            <div style={{ position: 'absolute', top: 12, right: 12, display: 'flex', gap: 6, zIndex: 5 }}>
                <button
                    onClick={async () => {
                        try {
                            await exportAsPng(graphRef.current);
                            addToast('Graph exported as PNG', 'success');
                        } catch {
                            addToast('Export failed', 'error');
                        }
                    }}
                    style={exportBtnStyle}
                    title="Export as PNG"
                >
                    PNG
                </button>
                <button
                    onClick={async () => {
                        try {
                            await exportAsSvg(graphRef.current);
                            addToast('Graph exported as SVG', 'success');
                        } catch {
                            addToast('Export failed', 'error');
                        }
                    }}
                    style={exportBtnStyle}
                    title="Export as SVG"
                >
                    SVG
                </button>
            </div>
        </div>
    );
};

export default GraphViewer;
