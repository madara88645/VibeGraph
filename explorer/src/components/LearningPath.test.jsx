import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('reactflow', () => ({
  useReactFlow: () => ({ fitView: vi.fn() }),
}));

// Keep the real helper by default (so existing fetch-based tests work), but make
// it spy-able so we can drive the retry-exhausted / Retry-button UI directly
// without waiting on real backoff timers.
vi.mock('../utils/aiClient', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    fetchAiJsonWithRetry: vi.fn((...args) => actual.fetchAiJsonWithRetry(...args)),
  };
});

import LearningPath from './LearningPath';
import * as aiClient from '../utils/aiClient';

const NODES = [
  {
    id: 'main',
    data: {
      label: 'main',
      file: 'repo/main.py',
      type: 'function',
      entry_point: true,
    },
  },
  {
    id: 'helper',
    data: {
      label: 'helper',
      file: 'repo/utils.py',
      type: 'function',
    },
  },
];

const EDGES = [{ id: 'emain-helper', source: 'main', target: 'helper' }];

function renderLearningPath(props = {}) {
  const defaults = {
    selectedFile: 'repo/main.py',
    allNodes: NODES,
    allEdges: EDGES,
    onSelectNode: vi.fn(),
    onSelectFile: vi.fn(),
    isOpen: true,
    onToggle: vi.fn(),
    apiKey: '',
    selectedModel: 'anthropic/claude-haiku-4.5',
    topOffset: 84,
    aiReady: false,
    onOpenAiSettings: vi.fn(),
  };
  return render(<LearningPath {...defaults} {...props} />);
}

describe('LearningPath', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          selected_file: 'repo/main.py',
          steps: [
            {
              step: 1,
              node_id: 'main',
              node_name: 'main',
              file_path: 'repo/main.py',
              reason: 'Start at the real entry point.',
            },
            {
              step: 2,
              node_id: 'helper',
              node_name: 'helper',
              file_path: 'repo/utils.py',
              reason: 'Then follow the call to helper.',
            },
          ],
        }),
    });
  });

  it('fetches without requiring an AI key and sends graph payload', async () => {
    const onOpenAiSettings = vi.fn();

    renderLearningPath({ onOpenAiSettings });

    await waitFor(() => {
      expect(screen.getByText('main')).toBeInTheDocument();
    });

    expect(onOpenAiSettings).not.toHaveBeenCalled();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/learning-path',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(String),
      })
    );
    const body = JSON.parse(globalThis.fetch.mock.calls[0][1].body);
    expect(body.nodes).toEqual(NODES);
    expect(body.edges).toEqual(EDGES);
    expect(body.selected_file).toBe('repo/main.py');
  });

  it('positions the panel using the provided top offset', () => {
    renderLearningPath({ allNodes: [], topOffset: 132 });

    expect(screen.getByLabelText('Close Learning Path').closest('#learning-path-panel')).toHaveStyle({
      top: '132px',
    });
  });

  it('renders step reason and selects returned node/file on navigation', async () => {
    const user = userEvent.setup();
    const onSelectFile = vi.fn();
    const onSelectNode = vi.fn();

    renderLearningPath({ onSelectFile, onSelectNode });

    await waitFor(() => {
      expect(screen.getByText('Start at the real entry point.')).toBeInTheDocument();
    });

    await user.click(screen.getByLabelText('Next step'));

    expect(onSelectFile).toHaveBeenCalledWith('repo/utils.py');
    expect(onSelectNode).toHaveBeenCalledWith(NODES[1]);
    expect(screen.getByText('Then follow the call to helper.')).toBeInTheDocument();
  });

  it('renders separate controls, metadata, and description regions for the active step', async () => {
    renderLearningPath();

    const controls = await screen.findByTestId('learning-path-controls');
    const metadata = await screen.findByTestId('learning-path-metadata');
    const description = await screen.findByTestId('learning-path-description');

    expect(controls).toBeInTheDocument();
    expect(metadata).toBeInTheDocument();
    expect(description).toBeInTheDocument();

    expect(screen.getByLabelText('Previous step')).toBeVisible();
    expect(screen.getByLabelText('Next step')).toBeVisible();
    expect(screen.getByLabelText('Close Learning Path')).toBeVisible();
    expect(metadata).toHaveTextContent('main');
    expect(metadata).toHaveTextContent('main.py');
    expect(description).toHaveTextContent('Start at the real entry point.');
  });

  it('exposes full node, file, and description values via title tooltips', async () => {
    const longReason = 'Trace the real entry point before branching into helper logic so the learning path has clear context.';

    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          steps: [
            {
              step: 1,
              node_id: 'main',
              node_name: 'main',
              file_path: 'repo/main.py',
              reason: longReason,
            },
          ],
        }),
    });

    renderLearningPath();

    const metadata = await screen.findByTestId('learning-path-metadata');
    const description = screen.getByTestId('learning-path-description');

    expect(screen.getByText('main')).toHaveAttribute('title', 'main');
    expect(screen.getByText('main.py')).toHaveAttribute('title', 'repo/main.py');
    expect(metadata).toBeInTheDocument();
    expect(description).toHaveAttribute('title', longReason);
  });

  it('fetches learning path when no file is selected but nodes exist (repo-wide path)', async () => {
    renderLearningPath({ selectedFile: null });

    await waitFor(() => {
      expect(screen.getByText('main')).toBeInTheDocument();
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/learning-path',
      expect.objectContaining({
        method: 'POST',
      })
    );
    const body = JSON.parse(globalThis.fetch.mock.calls[0][1].body);
    expect(body.selected_file).toBeNull();
  });

  it('renders "Upload a project" empty state when graph is empty', () => {
    renderLearningPath({ allNodes: [], selectedFile: null });
    expect(screen.getByText('Upload a project to build a learning path')).toBeInTheDocument();
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });

  it('renders "No path generated." when fetch returns no steps', async () => {
    globalThis.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ steps: [] }),
    });

    renderLearningPath();

    await waitFor(() => {
      expect(screen.getByText('No path generated.')).toBeInTheDocument();
    });
  });

  it('shows "Building learning path..." while fetching', async () => {
    let resolveFetch;
    globalThis.fetch.mockReturnValueOnce(new Promise(resolve => {
        resolveFetch = resolve;
    }));

    renderLearningPath();
    
    expect(screen.getByText('Building learning path...')).toBeInTheDocument();
    
    resolveFetch({ ok: true, json: () => Promise.resolve({ steps: [] }) });
  });

  it('shows the error message and a Retry button when the request ultimately fails', async () => {
    aiClient.fetchAiJsonWithRetry.mockRejectedValueOnce(
      Object.assign(new Error('Request failed (503)'), { status: 503 }),
    );

    renderLearningPath();

    expect(await screen.findByText('Request failed (503)')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /retry building learning path/i }),
    ).toBeInTheDocument();
  });

  it('refetches and renders the path when the Retry button is clicked', async () => {
    const user = userEvent.setup();
    // First attempt fails; the click then falls through to the real helper,
    // which hits the default success fetch mocked in beforeEach.
    aiClient.fetchAiJsonWithRetry.mockRejectedValueOnce(
      Object.assign(new Error('Request failed (503)'), { status: 503 }),
    );

    renderLearningPath();

    const retryButton = await screen.findByRole('button', {
      name: /retry building learning path/i,
    });
    await user.click(retryButton);

    expect(await screen.findByText('main')).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /retry building learning path/i }),
    ).not.toBeInTheDocument();
  });

  it('closes on Escape key press when panel is open', async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    renderLearningPath({ isOpen: true, onToggle });

    await screen.findByText('Path status');

    await user.keyboard('{Escape}');

    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('does not close on Escape key press when panel is closed', async () => {
    const user = userEvent.setup();
    const onToggle = vi.fn();
    renderLearningPath({ isOpen: false, onToggle });

    await user.keyboard('{Escape}');

    expect(onToggle).not.toHaveBeenCalled();
  });
});
