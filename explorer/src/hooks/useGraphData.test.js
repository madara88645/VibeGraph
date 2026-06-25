import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useGraphData } from './useGraphData';

function createCachedGraph() {
  return {
    schemaVersion: 3,
    source: 'user_upload',
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
    graphMeta: null,
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

  it('drops legacy unversioned cache so old shared graphs do not appear as a user upload', async () => {
    localStorage.setItem(
      'vg_v1_graph',
      JSON.stringify({
        nodes: [
          {
            id: 'legacy',
            type: 'custom',
            data: {
              label: 'legacy',
              type: 'function',
              file: '.\\\\main.py',
              entry_point: true,
            },
            position: { x: 0, y: 0 },
          },
        ],
        edges: [],
      })
    );

    const setNodes = vi.fn();
    const setEdges = vi.fn();

    const { result } = renderHook(() => useGraphData(setNodes, setEdges));

    await waitFor(() => {
      expect(result.current.allNodes).toEqual([]);
    });

    expect(localStorage.getItem('vg_v1_graph')).toBeNull();
    expect(result.current.files).toEqual([]);
    expect(result.current.selectedFile).toBeNull();
  });

  it('clears the rendered graph when an empty graph is received', async () => {
    const setNodes = vi.fn();
    const setEdges = vi.fn();

    const { result } = renderHook(() => useGraphData(setNodes, setEdges));

    result.current.handleUploadSuccess({
      nodes: [
        {
          id: 'main',
          type: 'default',
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
    });

    await waitFor(() => {
      expect(result.current.allNodes).toHaveLength(1);
    });

    result.current.handleUploadSuccess({ nodes: [], edges: [] });

    await waitFor(() => {
      expect(result.current.allNodes).toEqual([]);
    });

    expect(result.current.selectedFile).toBeNull();
    expect(result.current.fileDependencies).toBeNull();
    expect(setNodes).toHaveBeenCalledWith([]);
    expect(setEdges).toHaveBeenCalledWith([]);
  });

  it('stores truncation metadata from uploads so the UI can explain summary graphs', async () => {
    const setNodes = vi.fn();
    const setEdges = vi.fn();

    const { result } = renderHook(() => useGraphData(setNodes, setEdges));

    result.current.handleUploadSuccess({
      nodes: [
        {
          id: 'main',
          type: 'default',
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
      meta: {
        truncated: true,
        kept_nodes: 1500,
        total_nodes: 2143,
        total_edges: 2601,
        kept_edges: 1888,
        budget: 1500,
      },
    });

    await waitFor(() => {
      expect(result.current.graphMeta).toEqual({
        truncated: true,
        kept_nodes: 1500,
        total_nodes: 2143,
        total_edges: 2601,
        kept_edges: 1888,
        budget: 1500,
      });
    });
  });
});

const DEMO_RESULT = {
  nodes: [{ id: 'n1', data: { file: 'a.py', entry_point: true } }],
  edges: [],
  meta: { truncated: false, total_nodes: 1, total_edges: 0, kept_nodes: 1, kept_edges: 0 },
};

describe('useGraphData source tagging', () => {
  beforeEach(() => localStorage.clear());

  it("stores source:'demo' in the graph cache when demo load passes source", () => {
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const { result } = renderHook(() => useGraphData(setNodes, setEdges));
    act(() => result.current.handleUploadSuccess(DEMO_RESULT, null, 'demo'));
    const cached = JSON.parse(localStorage.getItem(result.current.cacheKey));
    expect(cached.source).toBe('demo');
  });

  it("defaults to source:'user_upload' for a normal upload", () => {
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const { result } = renderHook(() => useGraphData(setNodes, setEdges));
    act(() => result.current.handleUploadSuccess(DEMO_RESULT));
    const cached = JSON.parse(localStorage.getItem(result.current.cacheKey));
    expect(cached.source).toBe('user_upload');
  });
});
