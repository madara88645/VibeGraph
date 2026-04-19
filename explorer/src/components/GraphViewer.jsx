import React, { useRef, memo } from 'react';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';

import { useToast } from '../hooks/useToast';
import { exportAsPng, exportAsSvg } from '../utils/exportGraph';
import CustomNode from './CustomNode';

const nodeTypes = {
  custom: CustomNode,
};

const minimapNodeColor = (node) => {
  if (node.data?.entry_point) return '#22c55e';
  switch (node.data?.type) {
    case 'function':
      return '#06b6d4';
    case 'class':
      return '#a855f7';
    default:
      return '#334155';
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
  const showToast = useToast();
  const hasGraph = nodes.length > 0 || edges.length > 0;

  const handleExportPng = async () => {
    try {
      await exportAsPng(graphRef.current);
      showToast('Graph exported as PNG', 'success');
    } catch {
      showToast('PNG export failed', 'error');
    }
  };

  const handleExportSvg = async () => {
    try {
      await exportAsSvg(graphRef.current);
      showToast('Graph exported as SVG', 'success');
    } catch {
      showToast('SVG export failed', 'error');
    }
  };

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
      <div
        style={{
          position: 'absolute',
          top: 12,
          right: 12,
          display: 'flex',
          gap: 6,
          zIndex: 5,
        }}
      >
        <button
          onClick={handleExportPng}
          style={exportBtnStyle}
          title="Export as PNG"
          aria-label="Export as PNG"
        >
          PNG
        </button>
        <button
          onClick={handleExportSvg}
          style={exportBtnStyle}
          title="Export as SVG"
          aria-label="Export as SVG"
        >
          SVG
        </button>
      </div>
      {!hasGraph ? (
        <div className="graph-empty-state" aria-live="polite">
          <span className="graph-empty-kicker">Upload-first workspace</span>
          <h2>Upload a project to start exploring.</h2>
          <p>Your last uploaded graph will come back here after refresh.</p>
        </div>
      ) : null}
    </div>
  );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap GraphViewer in memo() to prevent O(N) ReactFlow re-renders
// of the entire graph when the parent App state updates rapidly (e.g. during Ghost Runner).
export default memo(GraphViewer);
