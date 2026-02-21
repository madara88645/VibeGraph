import React from 'react';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
} from 'reactflow';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';

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

const GraphViewer = ({ nodes, edges, onNodesChange, onEdgesChange, onNodeClick }) => {
    return (
        <div style={{ height: '100%', width: '100%' }}>
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
                    maskColor="rgba(0, 0, 0, 0.7)"
                    style={{ borderRadius: '10px' }}
                />
                <Controls />
                <Background variant="dots" color="#1e1e30" gap={20} size={1} />
            </ReactFlow>
        </div>
    );
};

export default GraphViewer;
