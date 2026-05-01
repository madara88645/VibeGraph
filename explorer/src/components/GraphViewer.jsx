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



const GraphViewer = ({ nodes, edges, onNodesChange, onEdgesChange, onNodeClick, onRequestUpload }) => {
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
          <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
          <span>PNG</span>
        </button>
        <button
          onClick={handleExportSvg}
          className="export-btn"
          title="Export as SVG"
          aria-label="Export as SVG"
        >
          <svg aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>
          <span>SVG</span>
        </button>
      </div>
      {!hasGraph ? (
        <div className="graph-empty-state" aria-live="polite">
          <div className="empty-hero">
            <div className="empty-orb" aria-hidden="true">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <circle cx="5" cy="6" r="2" />
                <circle cx="19" cy="6" r="2" />
                <circle cx="5" cy="18" r="2" />
                <circle cx="19" cy="18" r="2" />
                <line x1="9.5" y1="10.5" x2="6.5" y2="7.5" />
                <line x1="14.5" y1="10.5" x2="17.5" y2="7.5" />
                <line x1="9.5" y1="13.5" x2="6.5" y2="16.5" />
                <line x1="14.5" y1="13.5" x2="17.5" y2="16.5" />
              </svg>
            </div>

            <h2>Visualize any Python codebase</h2>
            <p className="empty-subtitle">
              Upload a project and VibeGraph will map its functions, classes, and call relationships into an interactive graph you can explore with AI.
            </p>

            <button
              className="empty-upload-cta"
              onClick={onRequestUpload}
              id="empty-state-upload-btn"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              Upload your Python project
            </button>
            <span className="empty-shortcut">or drag a folder anywhere on this page</span>
          </div>

          <div className="empty-features">
            <div className="empty-feature-card">
              <span className="empty-feature-icon" aria-hidden="true">⚡</span>
              <span className="empty-feature-title">AI Explanations</span>
              <span className="empty-feature-desc">Click any node for instant, plain-language breakdowns at your level</span>
            </div>
            <div className="empty-feature-card">
              <span className="empty-feature-icon" aria-hidden="true">👻</span>
              <span className="empty-feature-title">Ghost Runner</span>
              <span className="empty-feature-desc">Watch an AI tracer walk through your call graph in real time</span>
            </div>
            <div className="empty-feature-card">
              <span className="empty-feature-icon" aria-hidden="true">💬</span>
              <span className="empty-feature-title">Code Chat</span>
              <span className="empty-feature-desc">Ask follow-up questions about any function or architecture decision</span>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

// PERFORMANCE OPTIMIZATION (Bolt):
// Wrap GraphViewer in memo() to prevent O(N) ReactFlow re-renders
// of the entire graph when the parent App state updates rapidly (e.g. during Ghost Runner).
export default memo(GraphViewer);
