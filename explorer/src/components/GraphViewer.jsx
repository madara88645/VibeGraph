import React, { useRef } from 'react';
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
          <Background variant="dots" color="rgba(16, 185, 129, 0.15)" gap={24} size={1} />
        </ReactFlow>
      </div>
      <div className="export-controls">
        <button
          onClick={handleExportPng}
          className="export-btn"
          title="Export as PNG"
          aria-label="Export as PNG"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
          <span>PNG</span>
        </button>
        <button
          onClick={handleExportSvg}
          className="export-btn"
          title="Export as SVG"
          aria-label="Export as SVG"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
          <span>SVG</span>
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

export default GraphViewer;
