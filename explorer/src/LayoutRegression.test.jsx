import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as mockReact from 'react';

import App from './App';

// Hoist variables so they are defined when mock factories run
const { graphDataState, mockOnResetSimulation, mockSetIsPlaying } = vi.hoisted(() => {
  const mockOnResetSimulation = vi.fn();
  const mockSetIsPlaying = vi.fn();

  const graphDataState = {
    allNodes: [{ id: 'node-1', data: { label: 'node-1', file: 'main.py', type: 'function' } }],
    allNodesMap: new Map([['node-1', { id: 'node-1', data: { label: 'node-1', file: 'main.py', type: 'function' } }]]),
    allEdges: [],
    selectedFile: 'main.py',
    setSelectedFile: vi.fn(),
    files: ['main.py'],
    nodeStats: {},
    fileDependencies: [],
    handleUploadSuccess: vi.fn(),
    currentDegreeMap: {},
    graphMeta: {},
  };

  return { graphDataState, mockOnResetSimulation, mockSetIsPlaying };
});

// Setup minimal mocks for reactflow and other non-layout hooks
vi.mock('reactflow', () => {
  return {
    default: ({ nodes, onNodeClick }) => (
      <div data-testid="reactflow">
        {nodes.map((node) => (
          <button key={node.id} onClick={(e) => onNodeClick?.(e, node)}>
            Click {node.id}
          </button>
        ))}
      </div>
    ),
    ReactFlowProvider: ({ children }) => <>{children}</>,
    useNodesState: (initial) => {
      const [ns, setNs] = mockReact.useState(initial || []);
      return [ns, setNs, vi.fn()];
    },
    useEdgesState: (initial) => {
      const [es, setEs] = mockReact.useState(initial || []);
      return [es, setEs, vi.fn()];
    },
    useReactFlow: () => ({
      getNodes: () => [],
      getEdges: () => [],
      setNodes: vi.fn(),
      setEdges: vi.fn(),
    }),
    MiniMap: () => null,
    Controls: () => null,
    Background: () => null,
  };
});

// Mock scrollIntoView spy
const scrollIntoViewSpy = vi.fn();
window.HTMLElement.prototype.scrollIntoView = scrollIntoViewSpy;

vi.mock('./hooks/useTheme', () => ({
  useTheme: () => ({ theme: 'dark', toggleTheme: vi.fn() }),
}));

vi.mock('./hooks/useToast', () => ({
  ToastContext: mockReact.createContext(null),
  useToast: () => vi.fn(),
}));

vi.mock('./hooks/useGraphData', () => {
  return {
    useGraphData: (setNodes, setEdges) => {
      mockReact.useEffect(() => {
        setNodes(graphDataState.allNodes);
        setEdges(graphDataState.allEdges);
      }, [setNodes, setEdges]);
      return graphDataState;
    },
  };
});

vi.mock('./hooks/useGhostRunner', () => ({
  useGhostRunner: () => ({
    isPlaying: false,
    setIsPlaying: mockSetIsPlaying,
    stepCount: 0,
    speed: 2500,
    setSpeed: vi.fn(),
    currentLabel: '',
    onResetSimulation: mockOnResetSimulation,
    strategy: 'smart',
    setStrategy: vi.fn(),
    mode: 'auto',
    setMode: vi.fn(),
    visitedCount: 0,
    totalNodes: 1,
    availableNextNodes: [],
    onUserChooseNext: vi.fn(),
    narration: null,
    runSummary: null,
    ghostTutorial: null,
    stepSummaries: [],
  }),
}));

describe('Layout Regression Test for Issue #435', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    scrollIntoViewSpy.mockClear();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('does not trigger scrollIntoView on hidden chat elements when drawer is closed during streaming', async () => {
    globalThis.fetch = vi.fn().mockImplementation((url) => {
      if (url.includes('/api/ai-config')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              provider: 'openrouter',
              defaultModel: 'google/gemini-3.1-flash-lite',
              allowedModels: ['google/gemini-3.1-flash-lite'],
              requiresUserKey: false,
            }),
        });
      }
      if (url.includes('/api/chat/stream')) {
        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(new TextEncoder().encode('data: First chunk\n\n'));
            controller.enqueue(new TextEncoder().encode('data: Second chunk\n\n'));
            controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'));
            controller.close();
          },
        });
        return Promise.resolve({
          ok: true,
          body: stream,
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ explanation: 'technical explanation content' }),
      });
    });

    const user = userEvent.setup();
    const { container } = render(<App />);

    // Wait for the app to load and ensure main components are present
    await waitFor(() => {
      expect(screen.getByText('VibeGraph Explorer')).toBeInTheDocument();
    });

    // 1. Select a node in the graph
    const nodeBtn = screen.getByText('Click node-1');
    await user.click(nodeBtn);

    // Wait for explanation panel to open
    await waitFor(() => {
      expect(screen.getByLabelText('Close Explanation Panel')).toBeInTheDocument();
    });

    // 2. Open the Chat FAB
    const openChatBtn = screen.getByLabelText('Open Chat');
    await user.click(openChatBtn);

    // 3. Ask a question to start the stream
    const chatInput = screen.getByPlaceholderText('Ask a question...');
    await user.type(chatInput, 'What does this node do?');
    
    const sendBtn = screen.getByLabelText('Send message');
    await user.click(sendBtn);

    // 4. Immediately close the Chat drawer
    const closeChatBtn = screen.getByLabelText('Close Chat');
    await user.click(closeChatBtn);
    expect(container.querySelector('.chat-drawer')).not.toHaveClass('open');

    // Clear mock history of scrollIntoViewSpy to isolate background updates
    scrollIntoViewSpy.mockClear();

    // 5. Wait for the response to render in the chat drawer (which means the stream has run)
    // Note: ReactMarkdown will render the text inside a paragraph or similar container
    await waitFor(() => {
      expect(screen.getByText(/First chunkSecond chunk/)).toBeInTheDocument();
    });

    // CRITICAL ASSERTION: scrollIntoView should NOT have been called while the drawer was closed!
    expect(scrollIntoViewSpy).not.toHaveBeenCalled();
  });
});
