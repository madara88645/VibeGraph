import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLatestRequestGuard } from './useLatestRequestGuard';

describe('useLatestRequestGuard', () => {
    it('starts at id 0 before any request begins', () => {
        const { result } = renderHook(() => useLatestRequestGuard());

        expect(result.current.isLatestRequest(0)).toBe(true);
        expect(result.current.isLatestRequest(1)).toBe(false);
    });

    it('returns a monotonically increasing id from beginRequest', () => {
        const { result } = renderHook(() => useLatestRequestGuard());

        let first, second;
        act(() => {
            first = result.current.beginRequest();
        });
        act(() => {
            second = result.current.beginRequest();
        });

        expect(first).toBe(1);
        expect(second).toBe(2);
        expect(second).toBeGreaterThan(first);
    });

    it('treats the most recently begun request as the latest', () => {
        const { result } = renderHook(() => useLatestRequestGuard());

        let requestId;
        act(() => {
            requestId = result.current.beginRequest();
        });

        expect(result.current.isLatestRequest(requestId)).toBe(true);
    });

    it('treats an older request id as stale once a newer request begins', () => {
        const { result } = renderHook(() => useLatestRequestGuard());

        let staleId;
        act(() => {
            staleId = result.current.beginRequest();
        });
        act(() => {
            result.current.beginRequest();
        });

        expect(result.current.isLatestRequest(staleId)).toBe(false);
    });

    it('invalidateRequests marks the current in-flight request as stale', () => {
        const { result } = renderHook(() => useLatestRequestGuard());

        let requestId;
        act(() => {
            requestId = result.current.beginRequest();
        });
        act(() => {
            result.current.invalidateRequests();
        });

        expect(result.current.isLatestRequest(requestId)).toBe(false);
    });

    it('a request begun after invalidateRequests is the new latest', () => {
        const { result } = renderHook(() => useLatestRequestGuard());

        act(() => {
            result.current.beginRequest();
        });
        act(() => {
            result.current.invalidateRequests();
        });

        let newRequestId;
        act(() => {
            newRequestId = result.current.beginRequest();
        });

        expect(result.current.isLatestRequest(newRequestId)).toBe(true);
    });
});
