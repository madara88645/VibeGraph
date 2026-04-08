import { renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useGraphData } from './useGraphData';

function createCachedGraph() {
  return {
    nodes: [
      {
        id: 'main',
        type: 'custom',
        data: {
          label: 'main',
          type: 'function',
          file: 'src/main.py',
          entry_point: true,
        },
        position: { x: 0, y: 0 },
      },
    ],
    edges: [],
  };
}

describe('useGraphData', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('seed fetch should stay disabled'));
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it('starts empty when the user has not uploaded a graph yet', async () => {
    const setNodes = vi.fn();
    const setEdges = vi.fn();

    const { result } = renderHook(() => useGraphData(setNodes, setEdges));

    await waitFor(() => {
      expect(result.current.allNodes).toEqual([]);
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(result.current.files).toEqual([]);
    expect(result.current.selectedFile).toBeNull();
  });

  it('restores the last uploaded graph from local storage without falling back to shared seed data', async () => {
    const cachedGraph = createCachedGraph();
    localStorage.setItem('vg_v1_graph', JSON.stringify(cachedGraph));

    const setNodes = vi.fn();
    const setEdges = vi.fn();

    const { result } = renderHook(() => useGraphData(setNodes, setEdges));

    await waitFor(() => {
      expect(result.current.allNodes).toHaveLength(1);
    });

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(result.current.files).toEqual(['src/main.py']);
    expect(result.current.selectedFile).toBe('src/main.py');
  });
});
