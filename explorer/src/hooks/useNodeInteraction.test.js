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
      })
    );

    await act(async () => {
      await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
    });
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(result.current.explanation).toEqual(mockResponse);

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
});
