import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

const mockOnResetSimulation = vi.fn();
const mockSetIsPlaying = vi.fn();
const mockSetActiveNodeId = vi.fn();
const mockHandleUploadSuccess = vi.fn();

vi.mock('reactflow', () => ({
    ReactFlowProvider: ({ children }) => <>{children}</>,
    useNodesState: () => [[], vi.fn(), vi.fn()],
    useEdgesState: () => [[], vi.fn(), vi.fn()],
}));

vi.mock('./hooks/useTheme', () => ({
    useTheme: () => ({ theme: 'dark', toggleTheme: vi.fn() }),
}));

vi.mock('./hooks/useNodeInteraction', () => ({
    useNodeInteraction: () => ({
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
    }),
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
    }),
}));

vi.mock('./hooks/useGraphData', () => ({
    useGraphData: () => ({
        allNodes: [],
        selectedFile: null,
        setSelectedFile: vi.fn(),
        files: [],
        nodeStats: {},
        handleUploadSuccess: mockHandleUploadSuccess,
    }),
}));

vi.mock('./components/GraphViewer', () => ({ default: () => <div>GraphViewer</div> }));
vi.mock('./components/ExplanationPanel', () => ({ default: () => null }));
vi.mock('./components/FileSidebar', () => ({ default: () => null }));
vi.mock('./components/CodePanel', () => ({ default: () => null }));
vi.mock('./components/SearchBar', () => ({ default: () => null }));
vi.mock('./components/ChatDrawer', () => ({ default: () => null }));
vi.mock('./components/LearningPath', () => ({ default: () => null }));
vi.mock('./components/SimulationControls', () => ({ default: () => null }));
vi.mock('./components/GhostNarration', () => ({ default: () => null }));
vi.mock('./components/GhostChoices', () => ({ default: () => null }));
vi.mock('./components/GhostRunSummary', () => ({ default: () => null }));
vi.mock('./components/ErrorBoundary', () => ({ default: ({ children }) => <>{children}</> }));
vi.mock('./components/Toast', () => ({
    ToastProvider: ({ children }) => <>{children}</>,
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
});
