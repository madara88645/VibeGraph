import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useGhostRunner } from './useGhostRunner';

// Covers the 'hubsFirst' and 'byFile' Ghost Runner traversal strategies,
// which had no direct test coverage — only 'smart', 'random', and
// 'entryFirst' were exercised in useGhostRunner.test.js. Both strategies are
// fully deterministic (no Math.random involved), so each step's target node
// can be asserted exactly.

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

const aiContext = {
  aiApiKey: 'user-key',
  selectedModel: 'anthropic/claude-haiku-4.5',
  aiReady: false,
  onRequireAiKey: vi.fn(),
};

describe('useGhostRunner hubsFirst/byFile strategies', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('hubsFirst starts at the highest-degree node, breaking ties by node order', () => {
    const nodes = [
      createNode('a', { file: 'a.py' }),
      createNode('b', { file: 'b.py' }),
      createNode('c', { file: 'c.py' }),
    ];
    const edges = [];
    const degreeMap = new Map([
      ['a', 1],
      ['b', 3], // tied for highest degree with 'c', but appears first
      ['c', 3],
    ]);
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const setCodePanelNode = vi.fn();

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, aiContext, degreeMap)
    );

    act(() => {
      result.current.setStrategy('hubsFirst');
      result.current.setIsPlaying(true);
    });

    expect(result.current.activeNodeId).toBe('b');
  });

  it('hubsFirst prefers the highest-degree outgoing target, then jumps to the next highest-degree unvisited node once local edges are exhausted', () => {
    const nodes = [
      createNode('start'),
      createNode('lowDeg'),
      createNode('highDeg'),
      createNode('remoteHub'),
    ];
    const edges = [
      { id: 'e1', source: 'start', target: 'lowDeg' },
      { id: 'e2', source: 'start', target: 'highDeg' },
    ];
    const degreeMap = new Map([
      ['start', 10],
      ['lowDeg', 1],
      ['highDeg', 5],
      ['remoteHub', 9],
    ]);
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const setCodePanelNode = vi.fn();

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, aiContext, degreeMap)
    );

    act(() => {
      result.current.setStrategy('hubsFirst');
      result.current.setIsPlaying(true);
    });
    expect(result.current.activeNodeId).toBe('start');

    // 'start' has two outgoing edges; hubsFirst should follow the higher-degree one.
    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.activeNodeId).toBe('highDeg');

    // 'highDeg' has no outgoing edges; hubsFirst should jump to the highest-degree
    // remaining unvisited node overall ('remoteHub', degree 9) rather than the
    // lower-degree 'lowDeg' (degree 1).
    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.activeNodeId).toBe('remoteHub');

    // Only 'lowDeg' remains.
    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.activeNodeId).toBe('lowDeg');

    // All nodes visited — the runner should stop rather than looping forever.
    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.isPlaying).toBe(false);
  });

  it('byFile groups traversal by file, visiting every node of a file before moving to the next', () => {
    // Files are interleaved in the nodes array: f1, f2, f1, f2.
    // A naive nodes-array-order traversal would visit a, b, c, d in that order;
    // byFile must instead finish 'f1' (a, c) before touching 'f2' (b, d).
    const nodes = [
      createNode('a', { file: 'f1.py' }),
      createNode('b', { file: 'f2.py' }),
      createNode('c', { file: 'f1.py' }),
      createNode('d', { file: 'f2.py' }),
    ];
    const edges = [];
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const setCodePanelNode = vi.fn();

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, aiContext)
    );

    act(() => {
      result.current.setStrategy('byFile');
      result.current.setIsPlaying(true);
    });
    expect(result.current.activeNodeId).toBe('a');

    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.activeNodeId).toBe('c'); // stays in f1 before moving to f2

    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.activeNodeId).toBe('b'); // moves to the next file's queue

    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.activeNodeId).toBe('d');

    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.isPlaying).toBe(false);
  });

  it('byFile prefers a connected same-file edge target over an earlier, unconnected same-file node', () => {
    // 'b' is same-file and appears before 'c' in the nodes array, but only 'c'
    // is reachable via an outgoing edge from 'a'. The edge-connected same-file
    // target must win over the plain node-order scan.
    const nodes = [
      createNode('a', { file: 'shared.py' }),
      createNode('b', { file: 'shared.py' }),
      createNode('c', { file: 'shared.py' }),
    ];
    const edges = [{ id: 'e1', source: 'a', target: 'c' }];
    const setNodes = vi.fn();
    const setEdges = vi.fn();
    const setCodePanelNode = vi.fn();

    const { result } = renderHook(() =>
      useGhostRunner(nodes, edges, setNodes, setEdges, setCodePanelNode, aiContext)
    );

    act(() => {
      result.current.setStrategy('byFile');
      result.current.setIsPlaying(true);
    });
    expect(result.current.activeNodeId).toBe('a');

    act(() => { vi.advanceTimersByTime(2600); });
    expect(result.current.activeNodeId).toBe('c');
  });
});
