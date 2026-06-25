import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import GhostTutorialPanel from './components/GhostTutorialPanel';
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
import { DemoContentProvider, useDemoContent } from './context/DemoContentContext';
import { loadDemoAiContent, loadDemoGraph } from './utils/loadDemoGraph';
import { getShortName } from './utils/stringUtils';

function shortenModelName(modelName) {
  return modelName.split('/').pop() || modelName;
}

const EXPLANATION_PANEL_CLOSE_MS = 300;

// Badge copy is deliberately honest: a present-but-unchecked key shows "Key Set",
// never "AI Ready". "AI Ready" is reserved for a server-provided key (no user key
// required) or a key that has actually produced a successful response.
const AI_STATUS_LABELS = {
  ready: 'AI Ready',
  set: 'Key Set',
  invalid: 'Key Invalid',
  needsKey: 'Key Needed',
};

function AppInner() {
  const showToast = useToast();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { theme, toggleTheme } = useTheme();
  const uploadRef = useRef(null);
  const headerRef = useRef(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [aiSettingsOpen, setAiSettingsOpen] = useState(false);
  const [apiKey, setApiKeyState] = useState(() => getStoredApiKey());
  const [selectedModel, setSelectedModelState] = useState(() => getStoredModel());
  const [draftApiKey, setDraftApiKey] = useState(() => getStoredApiKey());
  const [draftModel, setDraftModel] = useState(() => getStoredModel());
  const [aiConfig, setAiConfig] = useState(DEFAULT_AI_CONFIG);
  const [aiConfigError, setAiConfigError] = useState('');
  // True only after an AI request actually reports an auth/invalid-key error.
  const [keyInvalid, setKeyInvalid] = useState(false);
  const [learningPathTopOffset, setLearningPathTopOffset] = useState(84);
  const [showFirstSteps, setShowFirstSteps] = useState(true);
  const [showTutorial, setShowTutorial] = useState(true);

  const { isDemo, setDemoContent, clearDemoContent, getBakedExplanation, getCannedChats } =
    useDemoContent();


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
  const aiStatus = !aiConfig.requiresUserKey
    ? 'ready'
    : !apiKey.trim()
      ? 'needsKey'
      : keyInvalid
        ? 'invalid'
        : 'set';

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
      // A freshly saved/changed key is not yet known to be bad; let the next
      // request re-prove it rather than carrying over a stale "invalid" badge.
      setKeyInvalid(false);

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
    setKeyInvalid(false);
    showToast('Session API key cleared.', 'info');
  }, [showToast]);

  const aiContext = useMemo(
    () => ({
      aiApiKey: apiKey,
      selectedModel: effectiveModel,
      aiReady,
      onRequireAiKey: openAiSettings,
      onAuthError: () => setKeyInvalid(true),
      onAuthCleared: () => setKeyInvalid(false),
    }),
    [aiReady, apiKey, effectiveModel, openAiSettings]
  );

  const {
    allNodes,
    allNodesMap,
    allEdges,
    selectedFile,
    setSelectedFile,
    files,
    nodeStats,
    fileDependencies,
    graphMeta,
    handleUploadSuccess,
    currentDegreeMap,
  } = useGraphData(setNodes, setEdges);

  const hasGraph = allNodes.length > 0 || allEdges.length > 0;

  useEffect(() => {
    if (!hasGraph) {
      return;
    }

    const headerElement = headerRef.current;
    if (!headerElement) {
      return;
    }

    const updateLearningPathOffset = () => {
      const { bottom } = headerElement.getBoundingClientRect();
      setLearningPathTopOffset(Math.max(84, Math.round(bottom + 12)));
    };

    updateLearningPathOffset();

    if (typeof ResizeObserver === 'function') {
      const resizeObserver = new ResizeObserver(() => {
        updateLearningPathOffset();
      });
      resizeObserver.observe(headerElement);

      return () => {
        resizeObserver.disconnect();
      };
    }

    window.addEventListener('resize', updateLearningPathOffset);
    return () => {
      window.removeEventListener('resize', updateLearningPathOffset);
    };
  }, [hasGraph]);

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
  } = useNodeInteraction({ ...aiContext, allNodes, allEdges, getBakedExplanation });

  const explanationPanelOpen = Boolean(selectedNode);
  const [explanationPanelClosing, setExplanationPanelClosing] = useState(false);
  const explanationPanelCloseTimerRef = useRef(null);
  const explanationPanelLayoutOpen = explanationPanelOpen || explanationPanelClosing;

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
    ghostTutorial,
    stepSummaries,
  } = useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, aiContext, currentDegreeMap);

  const onUploadSuccess = useCallback(
    (result, _resetCallback, source) => {
      handleUploadSuccess(result, () => {
        resetInteractionState();
        onResetSimulation();
        setShowFirstSteps(true);
      }, source);
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
  const handleRequestUpload = useCallback(
    () => uploadRef.current?.openModal(),
    []
  );
  const handleLoadDemo = useCallback(async () => {
    try {
      const [data, ai] = await Promise.all([loadDemoGraph(), loadDemoAiContent()]);
      setDemoContent(ai);                 // ai may be null → context stays not-demo
      onUploadSuccess(data, undefined, 'demo');
      showToast('Demo project loaded successfully!', 'success');
    } catch (err) {
      showToast('Failed to load demo project: ' + err.message, 'error');
    }
  }, [onUploadSuccess, showToast, setDemoContent]);
  const handleSelectFile = useCallback(
    (file) => {
      setSelectedFile(file);
      setSidebarOpen(false);
    },
    [setSelectedFile]
  );
  const handleCloseExplanation = useCallback(() => {
    setExplanationPanelClosing(true);

    if (explanationPanelCloseTimerRef.current) {
      clearTimeout(explanationPanelCloseTimerRef.current);
    }

    explanationPanelCloseTimerRef.current = setTimeout(() => {
      setExplanationPanelClosing(false);
      explanationPanelCloseTimerRef.current = null;
    }, EXPLANATION_PANEL_CLOSE_MS);

    setSelectedNode(null);
  }, [setSelectedNode]);

  useEffect(() => () => {
    if (explanationPanelCloseTimerRef.current) {
      clearTimeout(explanationPanelCloseTimerRef.current);
    }
  }, []);
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
        collapsed={isSidebarCollapsed}
      />

      <div className="main-area">
        <button
          className={`sidebar-desktop-toggle-btn ${isSidebarCollapsed ? 'collapsed' : ''}`}
          onClick={() => setIsSidebarCollapsed(prev => !prev)}
          aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ transform: isSidebarCollapsed ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.25s ease' }}
          >
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>

        <div
          ref={headerRef}
          className={[
            'vibe-header',
            hasGraph ? 'vibe-header-with-export' : 'vibe-header-compact',
            explanationPanelLayoutOpen ? 'vibe-header-panel-open' : '',
          ].filter(Boolean).join(' ')}
        >
          <button
            className="hamburger-btn"
            onClick={handleToggleSidebar}
            title="Toggle sidebar"
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

          <img src="/vibegraph-logo.png" alt="VibeGraph" className="header-logo" />
          <h1>VibeGraph Explorer</h1>
          <span
            className={`status-badge ${
              aiStatus === 'invalid' || aiStatus === 'needsKey' ? 'status-badge-warning' : ''
            }`}
          >
            {AI_STATUS_LABELS[aiStatus]}
          </span>

          <span className="current-file-badge">
            Model: {shortenModelName(effectiveModel)}
          </span>

          {selectedFile ? (
            <span className="current-file-badge">
              File: {getShortName(selectedFile)}
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

          {hasGraph ? (
            <button
              className="header-action-btn"
              onClick={() => setLearningPathOpen((prev) => !prev)}
              title="Learning Path"
              aria-label="Learning Path"
              aria-controls="learning-path-panel"
              aria-expanded={learningPathOpen}
            >
              Learn
            </button>
          ) : null}
          
          <button
            className="header-action-btn"
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            <span aria-hidden="true">{theme === 'dark' ? 'Light' : 'Dark'}</span>
          </button>

          <ProjectUpload
            ref={uploadRef}
            onUploadSuccess={onUploadSuccess}
            uploadLimits={aiConfig.uploadLimits}
            onClearDemo={clearDemoContent}
            onLoadDemo={handleLoadDemo}
          />

          {hasGraph ? (
            <SearchBar
              allNodes={allNodes}
              onSelectNode={handleSelectNode}
              onSelectFile={setSelectedFile}
            />
          ) : null}
        </div>

        <div
          className={`graph-shell ${explanationPanelLayoutOpen ? 'graph-shell-panel-open' : ''}`}
          style={{ '--vibe-header-safe-bottom': `${learningPathTopOffset}px` }}
        >
          {hasGraph ? (
            <LearningPath
              selectedFile={selectedFile}
              allNodes={allNodes}
              allNodesMap={allNodesMap}
              allEdges={allEdges}
              onSelectNode={handleSelectNode}
              onSelectFile={setSelectedFile}
              isOpen={learningPathOpen}
              onToggle={handleCloseLearningPath}
              apiKey={apiKey}
              selectedModel={effectiveModel}
              topOffset={learningPathTopOffset}
            />
          ) : null}

          {hasGraph && showFirstSteps ? (
            <div
              className="first-steps-banner"
              role="region"
              aria-label="Getting started"
            >
              <div role="status" aria-live="polite">
                <strong>Graph loaded!</strong> Click any node for an AI explanation, open Chat for follow-up questions, or use Ghost Runner to trace execution.
              </div>
              <button
                className="first-steps-dismiss"
                onClick={() => setShowFirstSteps(false)}
                aria-label="Dismiss first steps message"
              >
                Got it
              </button>
            </div>
          ) : null}
          <ErrorBoundary>
            <GraphViewer
              nodes={nodes}
              edges={edges}
              graphMeta={graphMeta}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onRequestUpload={handleRequestUpload}
              onLoadDemo={handleLoadDemo}
            />
          </ErrorBoundary>

          {hasGraph ? (
            <>
              <GhostTutorialPanel
                ghostTutorial={ghostTutorial}
                stepSummaries={stepSummaries}
                totalNodes={totalNodes}
                showTutorial={showTutorial}
                onClose={() => setShowTutorial(false)}
              />

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
                showTutorial={showTutorial}
                onToggleTutorial={() => setShowTutorial((prev) => !prev)}
              />
            </>
          ) : null}


          <ExplanationPanel
            node={selectedNode}
            explanation={explanation}
            loading={loading}
            onClose={handleCloseExplanation}
            fetchExplanation={fetchExplanation}
            onOpenAiSettings={openAiSettings}
          />

          {hasGraph ? (
            <ErrorBoundary>
              <ChatDrawer
                selectedNode={selectedNode}
                allNodes={allNodes}
                allEdges={allEdges}
                isOpen={chatOpen}
                onToggle={handleToggleChat}
                apiKey={apiKey}
                selectedModel={effectiveModel}
                aiReady={aiReady}
                onOpenAiSettings={openAiSettings}
                isDemo={isDemo}
                getCannedChats={getCannedChats}
              />
            </ErrorBoundary>
          ) : null}
        </div>

        {hasGraph ? (
          <CodePanel
            activeNode={codePanelNode}
            isGhostRunning={isPlaying}
            isOpen={codePanelOpen}
            onToggle={handleToggleCodePanel}
          />
        ) : null}
      </div>

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
          <DemoContentProvider>
            <AppInner />
          </DemoContentProvider>
        </ReactFlowProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}
