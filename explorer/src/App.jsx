import React, { useCallback } from 'react';
import { ReactFlowProvider, useNodesState, useEdgesState } from 'reactflow';
import 'reactflow/dist/style.css';

import GraphViewer from './components/GraphViewer';
import ExplanationPanel from './components/ExplanationPanel';
import FileSidebar from './components/FileSidebar';
import CodePanel from './components/CodePanel';
import SearchBar from './components/SearchBar';
import ChatDrawer from './components/ChatDrawer';
import LearningPath from './components/LearningPath';
import ProjectUpload from './components/ProjectUpload';
import SimulationControls from './components/SimulationControls';

// Custom Hooks
import { useGraphData } from './hooks/useGraphData';
import { useGhostRunner } from './hooks/useGhostRunner';
import { useNodeInteraction } from './hooks/useNodeInteraction';

function AppInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // 1. Interaction State & Handlers
  const {
    selectedNode,
    setSelectedNode,
    explanation,
    loading,
    codePanelOpen,
    setCodePanelOpen,
    codePanelNode,
    setCodePanelNode,
    chatOpen,
    setChatOpen,
    learningPathOpen,
    setLearningPathOpen,
    fetchExplanation,
    handleSelectNode,
    onNodeClick,
    resetInteractionState
  } = useNodeInteraction();

  // 2. Ghost Runner State & Handlers
  const {
    isPlaying,
    setIsPlaying,
    stepCount,
    speed,
    setSpeed,
    currentLabel,
    onResetSimulation,
    setActiveNodeId
  } = useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode);

  // 3. Graph Data & Global File State
  const {
    allNodes,
    selectedFile,
    setSelectedFile,
    files,
    nodeStats,
    handleUploadSuccess
  } = useGraphData(setNodes, setEdges);

  // Helper for Upload component that resets simulation and selection
  const onUploadSuccess = useCallback((result) => {
    handleUploadSuccess(result, () => {
      resetInteractionState();
      setIsPlaying(false);
      setActiveNodeId(null);
    });
  }, [handleUploadSuccess, resetInteractionState, setIsPlaying, setActiveNodeId]);

  const handleToggleSimulation = useCallback(() => setIsPlaying(prev => !prev), [setIsPlaying]);
  const handleCloseExplanation = useCallback(() => setSelectedNode(null), [setSelectedNode]);
  const handleToggleChat = useCallback(() => setChatOpen(prev => !prev), [setChatOpen]);
  const handleToggleCodePanel = useCallback(() => setCodePanelOpen(prev => !prev), [setCodePanelOpen]);
  const handleToggleLearningPath = useCallback(() => setLearningPathOpen(false), [setLearningPathOpen]);

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <FileSidebar
        files={files}
        selectedFile={selectedFile}
        onSelectFile={setSelectedFile}
        nodeStats={nodeStats}
      />

      {/* Main Area */}
      <div className="main-area">
        <div className="vibe-header">
          <h1>⚡ Vibe Learning</h1>
          <span className="status-badge">AI Active</span>
          {selectedFile && (
            <span className="current-file-badge">
              📄 {selectedFile.split(/[/\\]/).pop()}
            </span>
          )}
          <button
            className="header-action-btn"
            onClick={() => setLearningPathOpen(true)}
            title="Learning Path"
          >
            🎯 Learn
          </button>

          <ProjectUpload onUploadSuccess={onUploadSuccess} />

          <SearchBar
            allNodes={allNodes}
            onSelectNode={handleSelectNode}
            onSelectFile={setSelectedFile}
          />
        </div>

        {/* Graph */}
        <div className="graph-shell">
          <GraphViewer
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
          />

          <SimulationControls
            isPlaying={isPlaying}
            onToggle={handleToggleSimulation}
            onReset={onResetSimulation}
            stepCount={stepCount}
            speed={speed}
            onSpeedChange={setSpeed}
            currentLabel={currentLabel}
          />

          <ExplanationPanel
            node={selectedNode}
            explanation={explanation}
            loading={loading}
            onClose={handleCloseExplanation}
            fetchExplanation={fetchExplanation}
          />

          {/* Chat Drawer */}
          <ChatDrawer
            selectedNode={selectedNode}
            allNodes={allNodes}
            isOpen={chatOpen}
            onToggle={handleToggleChat}
          />
        </div>

        {/* Code Panel — Bottom */}
        <CodePanel
          activeNode={codePanelNode}
          isGhostRunning={isPlaying}
          isOpen={codePanelOpen}
          onToggle={handleToggleCodePanel}
        />
      </div>

      {/* Learning Path Overlay */}
      <LearningPath
        selectedFile={selectedFile}
        allNodes={allNodes}
        onSelectNode={handleSelectNode}
        onSelectFile={setSelectedFile}
        isOpen={learningPathOpen}
        onToggle={handleToggleLearningPath}
      />
    </div>
  );
}

// Wrap with ReactFlowProvider so SearchBar and LearningPath can use useReactFlow()
export default function App() {
  return (
    <ReactFlowProvider>
      <AppInner />
    </ReactFlowProvider>
  );
}
