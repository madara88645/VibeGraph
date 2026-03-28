import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
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
            json: () => Promise.resolve({ narration: 'step', relationship: '', importance: 'low' }),
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
            useGhostRunner(nodes, edges, setNodes, setEdges, vi.fn())
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
        const edges = [{ id: 'e1', source: 'main', target: 'ext', className: 'external-edge', style: { stroke: '#999' } }];
        const setNodes = vi.fn();
        const setEdges = vi.fn();

        const { result } = renderHook(() =>
            useGhostRunner(nodes, edges, setNodes, setEdges, vi.fn())
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
        const nodes = [
            createNode('main', { entry_point: true }),
            createNode('helper'),
        ];
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
                    ghostBaseStyle: { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 },
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
            useGhostRunner(nodes, latestEdges, setNodes, setEdges, vi.fn())
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
});
