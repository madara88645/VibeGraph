import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('reactflow', () => ({
  useReactFlow: () => ({ fitView: vi.fn() }),
}));

import LearningPath from './LearningPath';

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

  it('renders step reason and selects returned node/file on navigation', async () => {
    const user = userEvent.setup();
    const onSelectFile = vi.fn();
    const onSelectNode = vi.fn();

    renderLearningPath({ onSelectFile, onSelectNode });

    await waitFor(() => {
      expect(screen.getByText('Start at the real entry point.')).toBeInTheDocument();
    });

    await user.click(screen.getByLabelText('Next Step'));

    expect(onSelectFile).toHaveBeenCalledWith('repo/utils.py');
    expect(onSelectNode).toHaveBeenCalledWith(NODES[1]);
    expect(screen.getByText('Then follow the call to helper.')).toBeInTheDocument();
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
});
