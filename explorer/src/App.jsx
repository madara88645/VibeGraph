import React, { useCallback, useState } from 'react';
import { ReactFlowProvider, useEdgesState, useNodesState } from 'reactflow';
import 'reactflow/dist/style.css';

import ChatDrawer from './components/ChatDrawer';
import CodePanel from './components/CodePanel';
import ErrorBoundary from './components/ErrorBoundary';
import ExplanationPanel from './components/ExplanationPanel';
import FileSidebar from './components/FileSidebar';
import GhostChoices from './components/GhostChoices';
import GhostNarration from './components/GhostNarration';
import GhostRunSummary from './components/GhostRunSummary';
import GraphViewer from './components/GraphViewer';
import LearningPath from './components/LearningPath';
import ProjectUpload from './components/ProjectUpload';
import SearchBar from './components/SearchBar';
import SimulationControls from './components/SimulationControls';
import { ToastProvider } from './components/Toast';
import { useGhostRunner } from './hooks/useGhostRunner';
import { useGraphData } from './hooks/useGraphData';
import { useNodeInteraction } from './hooks/useNodeInteraction';
import { useTheme } from './hooks/useTheme';

function AppInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
    resetInteractionState,
  } = useNodeInteraction();

  const {
    isPlaying,
    setIsPlaying,
    stepCount,
    speed,
    setSpeed,
    currentLabel,
    onResetSimulation,
    strategy,
    setStrategy,
    mode,
    setMode,
    visitedCount,
    totalNodes,
    availableNextNodes,
    onUserChooseNext,
    narration,
    runSummary,
  } = useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode);

  const {
    allNodes,
    selectedFile,
    setSelectedFile,
    files,
    nodeStats,
    handleUploadSuccess,
  } = useGraphData(setNodes, setEdges);

  const onUploadSuccess = useCallback(
    (result) => {
      handleUploadSuccess(result, () => {
        resetInteractionState();
        onResetSimulation();
      });
    },
    [handleUploadSuccess, onResetSimulation, resetInteractionState]
  );

  const handleToggleSimulation = useCallback(
    () => setIsPlaying((prev) => !prev),
    [setIsPlaying]
  );
  const handleToggleChat = useCallback(
    () => setChatOpen((prev) => !prev),
    [setChatOpen]
  );
  const handleToggleCodePanel = useCallback(
    () => setCodePanelOpen((prev) => !prev),
    [setCodePanelOpen]
  );
  const handleCloseLearningPath = useCallback(
    () => setLearningPathOpen(false),
    [setLearningPathOpen]
  );
  const handleSelectFile = useCallback((file) => {
    setSelectedFile(file);
    setSidebarOpen(false);
  }, [setSelectedFile, setSidebarOpen]);
  const handleCloseExplanation = useCallback(
    () => setSelectedNode(null),
    [setSelectedNode]
  );
  const handleCloseSidebar = useCallback(
    () => setSidebarOpen(false),
    [setSidebarOpen]
  );
  const handleToggleSidebar = useCallback(
    () => setSidebarOpen((prev) => !prev),
    [setSidebarOpen]
  );

  return (
    <div className="app-shell">
      <div
        className={`sidebar-overlay ${sidebarOpen ? 'sidebar-open' : ''}`}
        onClick={handleCloseSidebar}
      />

      <FileSidebar
        files={files}
        selectedFile={selectedFile}
        onSelectFile={handleSelectFile}
        nodeStats={nodeStats}
        totalNodeCount={allNodes.length}
        mobileOpen={sidebarOpen}
      />

      <div className="main-area">
        <div className="vibe-header">
          <button
            className="hamburger-btn"
            onClick={handleToggleSidebar}
            aria-label="Toggle sidebar"
            aria-expanded={sidebarOpen}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              fontSize: '20px',
              padding: '4px 8px',
              display: 'none',
            }}
          >
            <span aria-hidden="true">{'\u2630'}</span>
          </button>
          <h1><span aria-hidden="true">{'\u26A1'}</span> Vibe Learning</h1>
          <span className="status-badge">AI Active</span>
          {selectedFile && (
            <span className="current-file-badge">
              <span aria-hidden="true">{'\uD83D\uDCC4'}</span> {selectedFile.split(/[/\\]/).pop()}
            </span>
          )}
          <button
            className="header-action-btn"
            onClick={() => setLearningPathOpen(true)}
            title="Learning Path"
            aria-expanded={learningPathOpen}
          >
            <span aria-hidden="true">{'\uD83C\uDFAF'}</span> Learn
          </button>

          <button
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            style={{
              background: 'none',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              padding: '6px 10px',
              fontSize: '14px',
            }}
          >
            <span aria-hidden="true">{theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19'}</span>
          </button>

          <ProjectUpload onUploadSuccess={onUploadSuccess} />

          <SearchBar
            allNodes={allNodes}
            onSelectNode={handleSelectNode}
            onSelectFile={setSelectedFile}
          />
        </div>

        <div className="graph-shell">
          <ErrorBoundary>
            <GraphViewer
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
            />
          </ErrorBoundary>

          <GhostNarration narration={narration} isPlaying={isPlaying} />
          <GhostChoices
            availableNextNodes={availableNextNodes}
            onChoose={onUserChooseNext}
            isPlaying={isPlaying}
            mode={mode}
          />
          <GhostRunSummary runSummary={runSummary} isPlaying={isPlaying} />

          <SimulationControls
            isPlaying={isPlaying}
            onToggle={handleToggleSimulation}
            onReset={onResetSimulation}
            stepCount={stepCount}
            speed={speed}
            onSpeedChange={setSpeed}
            currentLabel={currentLabel}
            strategy={strategy}
            onStrategyChange={setStrategy}
            mode={mode}
            onModeChange={setMode}
            visitedCount={visitedCount}
            totalNodes={totalNodes}
          />

          <ExplanationPanel
            node={selectedNode}
            explanation={explanation}
            loading={loading}
            onClose={handleCloseExplanation}
            fetchExplanation={fetchExplanation}
          />

          <ErrorBoundary>
            <ChatDrawer
              selectedNode={selectedNode}
              allNodes={allNodes}
              isOpen={chatOpen}
              onToggle={handleToggleChat}
            />
          </ErrorBoundary>
        </div>

        <CodePanel
          activeNode={codePanelNode}
          isGhostRunning={isPlaying}
          isOpen={codePanelOpen}
          onToggle={handleToggleCodePanel}
        />
      </div>

      <LearningPath
        selectedFile={selectedFile}
        allNodes={allNodes}
        onSelectNode={handleSelectNode}
        onSelectFile={setSelectedFile}
        isOpen={learningPathOpen}
        onToggle={handleCloseLearningPath}
      />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <ReactFlowProvider>
          <AppInner />
        </ReactFlowProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}
