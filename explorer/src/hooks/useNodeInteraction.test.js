import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { useNodeInteraction } from './useNodeInteraction';

describe('useNodeInteraction - explanation cache', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  const mockNode = {
    id: 'test_func',
    data: { file: 'test.py', label: 'test_func' },
  };
  const graphNodes = [mockNode, { id: 'caller_fn', data: {} }, { id: 'callee_fn', data: {} }];
  const graphEdges = [
    { source: 'caller_fn', target: 'test_func' },
    { source: 'test_func', target: 'callee_fn' },
  ];

  it('caches explanation and skips fetch on second call with same params', async () => {
    const mockResponse = { explanation: { technical: 'cached result' } };
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(result.current.explanation).toEqual(mockResponse);
    expect(JSON.parse(fetchSpy.mock.calls[0][1].body)).toMatchObject({
      callers: ['caller_fn'],
      callees: ['callee_fn'],
      neighbors: ['caller_fn', 'callee_fn'],
    });

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });

  it('fetches again for different tab or level combination', async () => {
    const mockResponse1 = { explanation: { technical: 'tech beginner' } };
    const mockResponse2 = { explanation: { analogy: 'analogy beginner' } };
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse1),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse2),
      });

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'analogy', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it('opens AI settings prompt instead of fetching when key is missing', async () => {
    const onRequireAiKey = vi.fn();
    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: '',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: false,
        onRequireAiKey,
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });

    expect(fetchSpy).not.toHaveBeenCalled();
    expect(onRequireAiKey).toHaveBeenCalledTimes(1);
    expect(result.current.explanation).toMatch(/Open AI Settings/i);
  });

  it('clears cache on resetInteractionState', async () => {
    const mockResponse = { explanation: { technical: 'result' } };
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    act(() => {
      result.current.resetInteractionState();
    });

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it('starts with the code panel closed by default', () => {
    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'deepseek/deepseek-v4-flash',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    expect(result.current.codePanelOpen).toBe(false);
    expect(result.current.chatOpen).toBe(false);
    expect(result.current.learningPathOpen).toBe(false);
  });
});

describe('useNodeInteraction - onNodeClick', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  const mockNode = {
    id: 'test_func',
    data: { file: 'test.py', label: 'test_func' },
  };
  const graphNodes = [mockNode, { id: 'caller_fn', data: {} }, { id: 'callee_fn', data: {} }];
  const graphEdges = [
    { source: 'caller_fn', target: 'test_func' },
    { source: 'test_func', target: 'callee_fn' },
  ];

  it('selects the node, clears explanation, and fetches technical intermediate', async () => {
    const mockResponse = {
      explanation: {
        technical: 'Explains the test function.',
        key_takeaway: 'Entry point for tests.',
      },
    };
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'anthropic/claude-haiku-4.5',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    act(() => {
      result.current.setExplanation({ explanation: { technical: 'stale' } });
    });
    expect(result.current.explanation).not.toBeNull();

    let clickPromise;
    act(() => {
      clickPromise = result.current.onNodeClick({}, mockNode);
    });

    expect(result.current.selectedNode).toEqual(mockNode);
    expect(result.current.explanation).toBeNull();
    expect(result.current.loading).toBe(true);

    await act(async () => {
      await clickPromise;
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.explanation).toEqual(mockResponse);
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    const [url, options] = fetchSpy.mock.calls[0];
    expect(url).toBe('/api/explain');
    const body = JSON.parse(options.body);
    expect(body).toMatchObject({
      file_path: 'test.py',
      node_id: 'test_func',
      type: 'technical',
      level: 'intermediate',
      callers: ['caller_fn'],
      callees: ['callee_fn'],
      neighbors: ['caller_fn', 'callee_fn'],
    });
  });

  it('allows slower Vibe Teacher responses before timing out', async () => {
    const mockResponse = { explanation: { technical: 'slow but successful' } };
    const timeoutSpy = vi.spyOn(window, 'setTimeout');
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'deepseek/deepseek-v4-flash',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'intermediate');
    });

    const [, options] = fetchSpy.mock.calls[0];
    expect(options.signal).toBeInstanceOf(AbortSignal);
    expect(timeoutSpy).toHaveBeenCalledWith(expect.any(Function), 75000);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it('shows a slow-teacher message when the explanation request times out', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(
      new DOMException('The operation was aborted.', 'AbortError')
    );

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'deepseek/deepseek-v4-flash',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'intermediate');
    });

    expect(result.current.explanation).toMatch(/taking longer than usual/i);
  });
  it('shows a connectivity message when the explanation request fails to reach the backend', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'));

    const { result } = renderHook(() =>
      useNodeInteraction({
        aiApiKey: 'user-key',
        selectedModel: 'deepseek/deepseek-v4-flash',
        aiReady: true,
        onRequireAiKey: vi.fn(),
        allNodes: graphNodes,
        allEdges: graphEdges,
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'intermediate');
    });
    expect(result.current.explanation).toMatch(/could not connect to vibe teacher/i);
  });
});

describe('useNodeInteraction - API key namespacing & auth signal', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  const mockNode = {
    id: 'test_func',
    data: { file: 'test.py', label: 'test_func' },
  };
  const graphNodes = [mockNode];
  const graphEdges = [];

  function renderWithKey(key, extra = {}) {
    return renderHook(
      ({ aiApiKey }) =>
        useNodeInteraction({
          aiApiKey,
          selectedModel: 'anthropic/claude-haiku-4.5',
          aiReady: true,
          onRequireAiKey: vi.fn(),
          allNodes: graphNodes,
          allEdges: graphEdges,
          ...extra,
        }),
      { initialProps: { aiApiKey: key } }
    );
  }

  it('does not reuse a cached explanation across different API keys', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ explanation: { technical: 'ok' } }),
    });

    const { result, rerender } = renderWithKey('valid-key');

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    // Same key -> cache hit, no new request.
    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    // Different key -> cache miss, so the new (possibly invalid) key is actually exercised.
    rerender({ aiApiKey: 'different-key' });
    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it('does not reuse a cached explanation across different models', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ explanation: { technical: 'ok' } }),
    });

    const { result, rerender } = renderHook(
      ({ selectedModel }) =>
        useNodeInteraction({
          aiApiKey: 'valid-key',
          selectedModel,
          aiReady: true,
          onRequireAiKey: vi.fn(),
          allNodes: graphNodes,
          allEdges: graphEdges,
        }),
      { initialProps: { selectedModel: 'anthropic/claude-haiku-4.5' } }
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    // Same model -> cache hit, no new request.
    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);

    // Different model -> cache miss, so the newly selected model is actually exercised.
    rerender({ selectedModel: 'deepseek/deepseek-v4-flash' });
    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(2);
  });

  it('signals an auth error, then clears it on a later successful explanation', async () => {
    const onAuthError = vi.fn();
    const onAuthCleared = vi.fn();
    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    const { result, rerender } = renderWithKey('bad-key', { onAuthError, onAuthCleared });

    fetchSpy.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid API key provided.' }),
    });
    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(onAuthError).toHaveBeenCalledTimes(1);
    expect(onAuthCleared).not.toHaveBeenCalled();

    fetchSpy.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ explanation: { technical: 'fixed' } }),
    });
    rerender({ aiApiKey: 'good-key' });
    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(onAuthCleared).toHaveBeenCalledTimes(1);
  });

  it('does not signal an auth error for non-auth failures', async () => {
    const onAuthError = vi.fn();
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new TypeError('Failed to fetch'));

    const { result } = renderWithKey('some-key', { onAuthError });

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(onAuthError).not.toHaveBeenCalled();
  });
});
