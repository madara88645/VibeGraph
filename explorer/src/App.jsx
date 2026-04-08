import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ReactFlowProvider, useEdgesState, useNodesState } from 'reactflow';
import 'reactflow/dist/style.css';

import AISettingsModal from './components/AISettingsModal';
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
import { useToast } from './hooks/useToast';
import {
  DEFAULT_AI_CONFIG,
  fetchAiConfig,
  getStoredApiKey,
  getStoredModel,
  setStoredApiKey,
  setStoredModel,
} from './utils/aiClient';

function shortenModelName(modelName) {
  return modelName.split('/').pop() || modelName;
}

function AppInner() {
  const showToast = useToast();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [aiSettingsOpen, setAiSettingsOpen] = useState(false);
  const [apiKey, setApiKeyState] = useState(() => getStoredApiKey());
  const [selectedModel, setSelectedModelState] = useState(() => getStoredModel());
  const [draftApiKey, setDraftApiKey] = useState(() => getStoredApiKey());
  const [draftModel, setDraftModel] = useState(() => getStoredModel());
  const [aiConfig, setAiConfig] = useState(DEFAULT_AI_CONFIG);
  const [aiConfigError, setAiConfigError] = useState('');

  useEffect(() => {
    let cancelled = false;

    const loadConfig = async () => {
      try {
        const config = await fetchAiConfig();
        if (cancelled) {
          return;
        }

        setAiConfig(config);
        setAiConfigError('');
        setSelectedModelState((currentModel) => {
          const allowedModels = config.allowedModels?.length
            ? config.allowedModels
            : DEFAULT_AI_CONFIG.allowedModels;
          const nextModel =
            currentModel && allowedModels.includes(currentModel)
              ? currentModel
              : config.defaultModel || allowedModels[0] || DEFAULT_AI_CONFIG.defaultModel;
          setStoredModel(nextModel);
          return nextModel;
        });
      } catch {
        if (cancelled) {
          return;
        }

        setAiConfig(DEFAULT_AI_CONFIG);
        setAiConfigError('Could not load backend AI config. Using safe local defaults.');
        setSelectedModelState((currentModel) => {
          const nextModel =
            currentModel && DEFAULT_AI_CONFIG.allowedModels.includes(currentModel)
              ? currentModel
              : DEFAULT_AI_CONFIG.defaultModel;
          setStoredModel(nextModel);
          return nextModel;
        });
        showToast('Could not load backend AI config. Using safe local defaults.', 'info');
      }
    };

    loadConfig();
    return () => {
      cancelled = true;
    };
  }, [showToast]);

  const effectiveModel =
    selectedModel || aiConfig.defaultModel || DEFAULT_AI_CONFIG.defaultModel;
  const aiReady = Boolean(apiKey.trim()) || !aiConfig.requiresUserKey;

  const openAiSettings = useCallback(
    (message) => {
      if (message) {
        showToast(message, 'info');
      }
      setDraftApiKey(apiKey);
      setDraftModel(effectiveModel);
      setAiSettingsOpen(true);
    },
    [apiKey, effectiveModel, showToast]
  );

  const handleSaveAiSettings = useCallback(
    ({ apiKey: nextApiKey, model }) => {
      const cleanedKey = nextApiKey.trim();
      const allowedModels = aiConfig.allowedModels?.length
        ? aiConfig.allowedModels
        : DEFAULT_AI_CONFIG.allowedModels;
      const nextModel =
        model && allowedModels.includes(model)
          ? model
          : aiConfig.defaultModel || allowedModels[0] || DEFAULT_AI_CONFIG.defaultModel;

      setApiKeyState(cleanedKey);
      setStoredApiKey(cleanedKey);
      setSelectedModelState(nextModel);
      setStoredModel(nextModel);

      showToast(
        cleanedKey
          ? 'AI settings saved for this session.'
          : 'Model saved. Add your OpenRouter key when you are ready.',
        'success'
      );
    },
    [aiConfig.allowedModels, aiConfig.defaultModel, showToast]
  );

  const handleClearAiKey = useCallback(() => {
    setApiKeyState('');
    setDraftApiKey('');
    setStoredApiKey('');
    showToast('Session API key cleared.', 'info');
  }, [showToast]);

  const aiContext = useMemo(
    () => ({
      aiApiKey: apiKey,
      selectedModel: effectiveModel,
      aiReady,
      onRequireAiKey: openAiSettings,
    }),
    [aiReady, apiKey, effectiveModel, openAiSettings]
  );

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
  } = useNodeInteraction(aiContext);

  const {
    allNodes,
    selectedFile,
    setSelectedFile,
    files,
    nodeStats,
    fileDependencies,
    handleUploadSuccess,
    currentDegreeMap,
  } = useGraphData(setNodes, setEdges);

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
  } = useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, aiContext, currentDegreeMap);

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
  const handleSelectFile = useCallback(
    (file) => {
      setSelectedFile(file);
      setSidebarOpen(false);
    },
    [setSelectedFile]
  );
  const handleCloseExplanation = useCallback(
    () => setSelectedNode(null),
    [setSelectedNode]
  );
  const handleCloseSidebar = useCallback(() => setSidebarOpen(false), []);
  const handleToggleSidebar = useCallback(
    () => setSidebarOpen((prev) => !prev),
    []
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
        fileDependencies={fileDependencies}
      />

      <div className="main-area">
        <div className="vibe-header">
          <button
            className="hamburger-btn"
            onClick={handleToggleSidebar}
            aria-label="Toggle sidebar"
            aria-controls="file-sidebar-panel"
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
            <span aria-hidden="true">Menu</span>
          </button>

          <h1>VibeGraph Explorer</h1>
          <span className={`status-badge ${aiReady ? '' : 'status-badge-warning'}`}>
            {aiReady ? 'AI Ready' : 'Key Needed'}
          </span>

          <span className="current-file-badge">
            Model: {shortenModelName(effectiveModel)}
          </span>

          {selectedFile ? (
            <span className="current-file-badge">
              File: {selectedFile.split(/[/\\]/).pop()}
            </span>
          ) : null}

          <button
            className="header-action-btn"
            onClick={() => openAiSettings()}
            title="AI Settings"
            aria-label="AI Settings"
          >
            AI Settings
          </button>

          <button
            className="header-action-btn"
            onClick={() => setLearningPathOpen((prev) => !prev)}
            title="Learning Path"
            aria-controls="learning-path-panel"
            aria-expanded={learningPathOpen}
          >
            Learn
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
            <span aria-hidden="true">{theme === 'dark' ? 'Light' : 'Dark'}</span>
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
              apiKey={apiKey}
              selectedModel={effectiveModel}
              aiReady={aiReady}
              onOpenAiSettings={openAiSettings}
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
        apiKey={apiKey}
        selectedModel={effectiveModel}
        aiReady={aiReady}
        onOpenAiSettings={openAiSettings}
      />

      <AISettingsModal
        isOpen={aiSettingsOpen}
        onClose={() => setAiSettingsOpen(false)}
        apiConfig={aiConfig}
        draftApiKey={draftApiKey}
        draftModel={draftModel}
        configError={aiConfigError}
        onSave={handleSaveAiSettings}
        onClear={handleClearAiKey}
        onDraftApiKeyChange={setDraftApiKey}
        onDraftModelChange={setDraftModel}
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
