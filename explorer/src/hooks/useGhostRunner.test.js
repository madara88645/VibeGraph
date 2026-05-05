import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useGhostRunner } from './useGhostRunner';

function createNode(id, overrides = {}) {
  return {
    id,
    data: {
      label: id,
      file: `${id}.py`,
      ...overrides,
    },
  };
}

describe('useGhostRunner', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          narration: 'step',
          relationship: '',
          importance: 'low',
        }),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('stops auto mode after visiting the last file-backed node', () => {
    const nodes = [createNode('main', { entry_point: true })];
    const edges = [];
    const setNodes = vi.fn();
    const setEdges = vi.fn();

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, vi.fn(), {
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
      })
    );

    act(() => {
      result.current.setStrategy('entryFirst');
      result.current.setIsPlaying(true);
    });

    act(() => {
      vi.advanceTimersByTime(2600);
    });

    expect(result.current.isPlaying).toBe(false);
    expect(result.current.visitedCount).toBe(1);
    expect(result.current.totalNodes).toBe(1);
  });

  it('does not count external placeholder nodes as visited progress', () => {
    const nodes = [
      createNode('main', { entry_point: true }),
      { id: 'ext', data: { label: 'external', isExternal: true, file: null } },
    ];
    const edges = [
      {
        id: 'e1',
        source: 'main',
        target: 'ext',
        className: 'external-edge',
        style: { stroke: '#999' },
      },
    ];
    const setNodes = vi.fn();
    const setEdges = vi.fn();

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, vi.fn(), {
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
      })
    );

    act(() => {
      result.current.setStrategy('entryFirst');
      result.current.setIsPlaying(true);
    });

    act(() => {
      vi.advanceTimersByTime(2600);
    });

    expect(result.current.visitedCount).toBe(1);
    expect(result.current.totalNodes).toBe(1);
  });

  it('preserves cycle edge styling while highlighting the active traversal edge', () => {
    const nodes = [createNode('main', { entry_point: true }), createNode('helper')];
    let latestEdges = [
      {
        id: 'forward',
        source: 'main',
        target: 'helper',
        className: '',
        animated: false,
        style: { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 },
        data: {
          ghostBaseClassName: '',
          ghostBaseAnimated: false,
          ghostBaseStyle: {
            stroke: 'rgba(148, 163, 184, 0.55)',
            strokeWidth: 3.5,
          },
        },
      },
      {
        id: 'cycle',
        source: 'helper',
        target: 'main',
        className: 'cycle-edge',
        animated: true,
        style: { stroke: '#f97316', strokeWidth: 3, strokeDasharray: '8 4' },
        data: {
          ghostBaseClassName: 'cycle-edge',
          ghostBaseAnimated: true,
          ghostBaseStyle: { stroke: '#f97316', strokeWidth: 3, strokeDasharray: '8 4' },
        },
      },
    ];
    const setNodes = vi.fn();
    const setEdges = vi.fn((updater) => {
      latestEdges = typeof updater === 'function' ? updater(latestEdges) : updater;
    });

    const { result } = renderHook(() =>
      useGhostRunner(nodes, latestEdges, setNodes, setEdges, vi.fn(), {
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
      })
    );

    act(() => {
      result.current.setStrategy('entryFirst');
      result.current.setIsPlaying(true);
    });

    act(() => {
      vi.advanceTimersByTime(2600);
    });

    const cycleEdge = latestEdges.find((edge) => edge.id === 'cycle');
    expect(cycleEdge.className).toBe('cycle-edge');
    expect(cycleEdge.style.stroke).toBe('#f97316');
    expect(cycleEdge.style.strokeDasharray).toBe('8 4');
  });

  it('entryFirst dead-end fallback picks unvisited entry point before regular file node', () => {
    // nodes order: [a (entry_point), c (file only), b (entry_point)]
    // 'c' comes before 'b' in the nodes array; naive nodes.find() would pick 'c' first.
    // The fallback must consult entryPointsRef and return 'b' (entry point) instead.
    vi.spyOn(Math, 'random').mockReturnValue(0); // forces pickRandomFromPool to select index 0 → 'a'
    const nodes = [
      createNode('a', { entry_point: true }),
      createNode('c'), // file-backed, NOT an entry point
      createNode('b', { entry_point: true }),
    ];
    const edges = [];
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const setCodePanelNode = vi.fn(); // stable reference avoids spurious game-loop re-runs

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, {
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
      })
    );

    act(() => {
      result.current.setStrategy('entryFirst');
      result.current.setIsPlaying(true);
    });
    // Step 1 fires within the above act: 'a' is picked (Math.random=0 → index 0 of entry points)

    act(() => { vi.advanceTimersByTime(2600); });
    // Step 2: 'a' has no outgoing edges; DFS stack empty; fallback via entryPointsRef picks 'b'
    // (not 'c', which appears earlier in the nodes array)
    expect(result.current.activeNodeId).toBe('b');
  });

  it('entryFirst dead-end fallback picks any file-backed node when no entry points remain unvisited', () => {
    const nodes = [
      createNode('a', { entry_point: true }),
      createNode('b'), // file-backed, NOT an entry point
    ];
    const edges = [];
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const setCodePanelNode = vi.fn(); // stable reference avoids spurious game-loop re-runs

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, {
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
      })
    );

    act(() => {
      result.current.setStrategy('entryFirst');
      result.current.setIsPlaying(true);
    });
    // Step 1 fires within the above act: 'a' is picked (only entry point)

    act(() => { vi.advanceTimersByTime(2600); });
    // Step 2: 'a' has no outgoing edges; DFS stack empty; no unvisited entry points remain;
    // falls back to 'b' (first unvisited file-backed node)
    expect(result.current.activeNodeId).toBe('b');
  });

  it('skips narration calls when AI is not ready', () => {
    const nodes = [createNode('main', { entry_point: true })];
    const edges = [];
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const onRequireAiKey = vi.fn();

    renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, vi.fn(), {
        aiApiKey: '',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: false,
        onRequireAiKey,
      })
    );

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(onRequireAiKey).not.toHaveBeenCalled();
  });
});
