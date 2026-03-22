import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useNodeInteraction } from './useNodeInteraction';

describe('useNodeInteraction - explanation cache', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    const mockNode = {
        id: 'test_func',
        data: { file: 'test.py', label: 'test_func' },
    };

    it('caches explanation and skips fetch on second call with same params', async () => {
        const mockResponse = { explanation: { technical: 'cached result' } };
        const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
            json: () => Promise.resolve(mockResponse),
        });

        const { result } = renderHook(() => useNodeInteraction());

        // First call — should fetch
        await act(async () => {
            await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
        });
        expect(fetchSpy).toHaveBeenCalledTimes(1);
        expect(result.current.explanation).toEqual(mockResponse);

        // Second call with same params — should use cache
        await act(async () => {
            await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
        });
        expect(fetchSpy).toHaveBeenCalledTimes(1); // No additional fetch
    });

    it('fetches again for different tab/level combination', async () => {
        const mockResponse1 = { explanation: { technical: 'tech beginner' } };
        const mockResponse2 = { explanation: { analogy: 'analogy beginner' } };
        const fetchSpy = vi.spyOn(globalThis, 'fetch')
            .mockResolvedValueOnce({ json: () => Promise.resolve(mockResponse1) })
            .mockResolvedValueOnce({ json: () => Promise.resolve(mockResponse2) });

        const { result } = renderHook(() => useNodeInteraction());

        await act(async () => {
            await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
        });
        expect(fetchSpy).toHaveBeenCalledTimes(1);

        // Different type — should fetch again
        await act(async () => {
            await result.current.fetchExplanation(mockNode, 'analogy', 'beginner');
        });
        expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    it('clears cache on resetInteractionState', async () => {
        const mockResponse = { explanation: { technical: 'result' } };
        const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
            json: () => Promise.resolve(mockResponse),
        });

        const { result } = renderHook(() => useNodeInteraction());

        // Populate cache
        await act(async () => {
            await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
        });
        expect(fetchSpy).toHaveBeenCalledTimes(1);

        // Reset clears cache
        act(() => {
            result.current.resetInteractionState();
        });

        // Same params should fetch again after reset
        await act(async () => {
            await result.current.fetchExplanation(mockNode, 'technical', 'beginner');
        });
        expect(fetchSpy).toHaveBeenCalledTimes(2);
    });
});
