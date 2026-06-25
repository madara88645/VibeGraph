import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import App from './App';
import { loadDemoGraph, loadDemoAiContent } from './utils/loadDemoGraph';

const mockOnResetSimulation = vi.fn();
const mockSetIsPlaying = vi.fn();
const mockSetActiveNodeId = vi.fn();
const mockHandleUploadSuccess = vi.fn();
let resizeObserverCallback = null;
let headerBottom = 72;
let mockAiContext = null;

const graphDataState = {
  allNodes: [],
  allNodesMap: new Map(),
  allEdges: [],
  selectedFile: null,
  setSelectedFile: vi.fn(),
  files: [],
  nodeStats: {},
  fileDependencies: [],
  handleUploadSuccess: mockHandleUploadSuccess,
  currentDegreeMap: {},
  graphMeta: {},
};

const nodeInteractionState = {
  selectedNode: null,
  setSelectedNode: vi.fn(),
  explanation: null,
  loading: false,
  codePanelOpen: false,
  setCodePanelOpen: vi.fn(),
  codePanelNode: null,
  setCodePanelNode: vi.fn(),
  chatOpen: false,
  setChatOpen: vi.fn(),
  learningPathOpen: false,
  setLearningPathOpen: vi.fn(),
  fetchExplanation: vi.fn(),
  handleSelectNode: vi.fn(),
  onNodeClick: vi.fn(),
  resetInteractionState: vi.fn(),
};

vi.mock('reactflow', () => ({
  ReactFlowProvider: ({ children }) => <>{children}</>,
  useNodesState: () => [[], vi.fn(), vi.fn()],
  useEdgesState: () => [[], vi.fn(), vi.fn()],
}));

vi.mock('./hooks/useTheme', () => ({
  useTheme: () => ({ theme: 'dark', toggleTheme: vi.fn() }),
}));

vi.mock('./hooks/useToast', () => ({
  useToast: () => vi.fn(),
}));

vi.mock('./hooks/useNodeInteraction', () => ({
  useNodeInteraction: (config) => {
    mockAiContext = config;
    return nodeInteractionState;
  },
}));

vi.mock('./hooks/useGhostRunner', () => ({
  useGhostRunner: () => ({
    isPlaying: false,
    setIsPlaying: mockSetIsPlaying,
    stepCount: 0,
    speed: 2500,
    setSpeed: vi.fn(),
    currentLabel: '',
    onResetSimulation: mockOnResetSimulation,
    setActiveNodeId: mockSetActiveNodeId,
    strategy: 'smart',
    setStrategy: vi.fn(),
    mode: 'auto',
    setMode: vi.fn(),
    visitedCount: 0,
    totalNodes: 0,
    availableNextNodes: [],
    onUserChooseNext: vi.fn(),
    narration: null,
    setNarration: vi.fn(),
    runSummary: null,
    ghostTutorial: null,
    stepSummaries: [],
  }),
}));

vi.mock('./hooks/useGraphData', () => ({
  useGraphData: () => graphDataState,
}));

vi.mock('./components/GraphViewer', () => ({
  default: ({ nodes = [], onLoadDemo }) =>
    nodes.length === 0 ? (
      <div>
        <div>Visualize your codebase</div>
        {onLoadDemo ? (
          <button type="button" onClick={() => onLoadDemo()}>
            load-demo
          </button>
        ) : null}
      </div>
    ) : (
      <div>GraphViewer</div>
    ),
}));

vi.mock('./utils/loadDemoGraph', () => ({
  loadDemoGraph: vi.fn(),
  loadDemoAiContent: vi.fn(),
}));
vi.mock('./components/ExplanationPanel', () => ({ default: () => null }));
vi.mock('./components/FileSidebar', () => ({
  default: ({ collapsed }) => <div>FileSidebar:{collapsed ? 'collapsed' : 'expanded'}</div>,
}));
vi.mock('./components/CodePanel', () => ({
  default: ({ isOpen }) => <div>CodePanel:{isOpen ? 'open' : 'closed'}</div>,
}));
vi.mock('./components/SearchBar', () => ({ default: () => <div>SearchBar</div> }));
vi.mock('./components/ChatDrawer', () => ({
  default: ({ isOpen }) => <div>ChatDrawer:{isOpen ? 'open' : 'closed'}</div>,
}));
vi.mock('./components/LearningPath', () => ({
  default: ({ isOpen, topOffset }) => (
    <div data-testid="learning-path" data-open={isOpen ? 'open' : 'closed'} data-top-offset={String(topOffset)}>
      LearningPath:{isOpen ? 'open' : 'closed'}
    </div>
  ),
}));
vi.mock('./components/SimulationControls', () => ({ default: () => <div>SimulationControls</div> }));
vi.mock('./components/GhostNarration', () => ({ default: () => null }));
vi.mock('./components/GhostChoices', () => ({ default: () => null }));
vi.mock('./components/GhostRunSummary', () => ({ default: () => null }));
vi.mock('./components/GhostTutorialPanel', () => ({ default: () => null }));
vi.mock('./components/ErrorBoundary', () => ({ default: ({ children }) => <>{children}</> }));
vi.mock('./components/Toast', () => ({
  ToastProvider: ({ children }) => <>{children}</>,
}));
vi.mock('./components/AISettingsModal', () => ({
  default: ({ isOpen, onClose }) =>
    isOpen ? (
      <div>
        <span>AI Settings</span>
        <button onClick={onClose}>Close AI Settings</button>
      </div>
    ) : null,
}));

vi.mock('./components/ProjectUpload', () => ({
  default: ({ onUploadSuccess }) => (
    <button onClick={() => onUploadSuccess({ nodes: [], edges: [] })}>
      Trigger Upload
    </button>
  ),
}));

describe('App upload flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resizeObserverCallback = null;
    headerBottom = 72;
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          provider: 'openrouter',
          defaultModel: 'google/gemini-3.1-flash-lite',
          allowedModels: [
            'deepseek/deepseek-v4-flash',
            'google/gemini-3.1-flash-lite',
          ],
          requiresUserKey: true,
        }),
    });
    globalThis.ResizeObserver = class {
      constructor(callback) {
        resizeObserverCallback = callback;
      }

      observe() {}
      disconnect() {}
    };
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(function mockRect() {
      if (this.classList?.contains('vibe-header')) {
        return { top: 16, bottom: headerBottom, left: 16, right: 600, width: 584, height: headerBottom - 16 };
      }

      return { top: 0, bottom: 0, left: 0, right: 0, width: 0, height: 0 };
    });
    sessionStorage.clear();
    localStorage.clear();
    Object.assign(graphDataState, {
      allNodes: [],
      allNodesMap: new Map(),
      allEdges: [],
      selectedFile: null,
      graphMeta: {},
    });
    Object.assign(nodeInteractionState, {
      selectedNode: null,
      explanation: null,
      loading: false,
      codePanelOpen: false,
      codePanelNode: null,
      chatOpen: false,
      learningPathOpen: false,
    });
    mockHandleUploadSuccess.mockImplementation((result, resetCallback) => {
      resetCallback?.(result);
    });
  });

  it('fully resets Ghost Runner state after a new upload succeeds', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByText('Trigger Upload'));

    expect(mockOnResetSimulation).toHaveBeenCalledTimes(1);
    expect(mockSetIsPlaying).not.toHaveBeenCalled();
    expect(mockSetActiveNodeId).not.toHaveBeenCalled();
  });

  it('opens the AI settings modal from the header', async () => {
    const user = userEvent.setup();
    render(<App />);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith('/api/ai-config');
    });

    await user.click(screen.getByRole('button', { name: /AI Settings/i }));

    expect(screen.getByText('Close AI Settings')).toBeInTheDocument();
  });

  it('starts in an upload-first layout with non-essential graph controls hidden', async () => {
    render(<App />);

    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith('/api/ai-config');
    });

    expect(screen.getByText('FileSidebar:collapsed')).toBeInTheDocument();
    expect(screen.queryByText('CodePanel:closed')).not.toBeInTheDocument();
    expect(screen.queryByText('ChatDrawer:closed')).not.toBeInTheDocument();
    expect(screen.queryByText('LearningPath:closed')).not.toBeInTheDocument();
    expect(screen.getByText('Visualize your codebase')).toBeInTheDocument();
    expect(screen.queryByText('SearchBar')).not.toBeInTheDocument();
    expect(screen.queryByText('SimulationControls')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Learning Path' })).not.toBeInTheDocument();
  });

  it('loads the bundled demo graph when the empty-state demo CTA is used', async () => {
    const user = userEvent.setup();
    const payload = { nodes: [{ id: 'demo' }], edges: [] };
    loadDemoGraph.mockResolvedValue(payload);

    render(<App />);
    await waitFor(() => {
      expect(globalThis.fetch).toHaveBeenCalledWith('/api/ai-config');
    });

    await user.click(screen.getByText('load-demo'));

    await waitFor(() => {
      expect(loadDemoGraph).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(mockHandleUploadSuccess).toHaveBeenCalledWith(payload, expect.any(Function), 'demo');
    });
  });

  it('shows the active model from backend config in the header', async () => {
    render(<App />);

    expect(await screen.findByText('Model: gemini-3.1-flash-lite')).toBeInTheDocument();
  });

  it('renders Learning Path inside the graph shell and updates its top offset from header size', async () => {
    graphDataState.allNodes = [{ id: 'main', data: { label: 'main', file: 'repo/main.py' } }];
    graphDataState.allNodesMap = new Map([['main', graphDataState.allNodes[0]]]);
    nodeInteractionState.learningPathOpen = true;

    const { container } = render(<App />);

    const learningPath = await screen.findByTestId('learning-path');
    const graphShell = container.querySelector('.graph-shell');

    expect(graphShell).not.toBeNull();
    expect(graphShell?.contains(learningPath)).toBe(true);
    await waitFor(() => {
      expect(learningPath).toHaveAttribute('data-top-offset', '84');
    });
    await waitFor(() => {
      expect(typeof resizeObserverCallback).toBe('function');
    });

    headerBottom = 96;
    act(() => {
      resizeObserverCallback?.([]);
    });

    await waitFor(() => {
      expect(learningPath).toHaveAttribute('data-top-offset', '108');
    });
  });

  it('shows "Key Needed" when a user key is required but none is set', async () => {
    render(<App />);

    expect(await screen.findByText('Key Needed')).toBeInTheDocument();
    expect(screen.queryByText('AI Ready')).not.toBeInTheDocument();
  });

  it('shows "Key Set" (not "AI Ready") for a present but unvalidated user key', async () => {
    sessionStorage.setItem('vg_v1_openrouter_key', 'sk-unvalidated');

    render(<App />);

    expect(await screen.findByText('Key Set')).toBeInTheDocument();
    expect(screen.queryByText('AI Ready')).not.toBeInTheDocument();
  });

  it('shows "AI Ready" only when the backend does not require a user key', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          provider: 'openrouter',
          defaultModel: 'google/gemini-3.1-flash-lite',
          allowedModels: ['google/gemini-3.1-flash-lite'],
          requiresUserKey: false,
        }),
    });

    render(<App />);

    expect(await screen.findByText('AI Ready')).toBeInTheDocument();
  });

  it('flips the badge to "Key Invalid" when an AI request reports an auth error', async () => {
    sessionStorage.setItem('vg_v1_openrouter_key', 'sk-bad');

    render(<App />);

    expect(await screen.findByText('Key Set')).toBeInTheDocument();

    act(() => {
      mockAiContext.onAuthError();
    });

    expect(await screen.findByText('Key Invalid')).toBeInTheDocument();
    expect(screen.queryByText('Key Set')).not.toBeInTheDocument();
  });

  it('loads pre-baked AI content alongside the demo graph and serves a baked explanation', async () => {
    const user = userEvent.setup();
    loadDemoGraph.mockResolvedValue({ nodes: [{ id: 'n1', data: { file: 'a.py' } }], edges: [] });
    loadDemoAiContent.mockResolvedValue({
      explanations: {
        n1: {
          snippet: 'def n1(): pass',
          levels: {
            beginner: { analogy: 'a', technical: 't', key_takeaway: 'k' },
            intermediate: { analogy: 'a2', technical: 't2', key_takeaway: 'k2' },
            advanced: { analogy: 'a3', technical: 't3', key_takeaway: 'k3' },
          },
        },
      },
      chat: [],
    });

    render(<App />);
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledWith('/api/ai-config'));
    await user.click(screen.getByText('load-demo'));

    await waitFor(() => expect(loadDemoAiContent).toHaveBeenCalledTimes(1));
  });
});
