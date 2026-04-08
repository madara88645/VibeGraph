import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';

describe('useTheme', () => {
    beforeEach(() => {
        localStorage.clear();
        document.documentElement.removeAttribute('data-theme');
        vi.restoreAllMocks();
    });

    it('returns current theme', () => {
        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBeDefined();
        expect(['light', 'dark']).toContain(result.current.theme);
    });

    it('defaults to dark when no saved theme and no system preference', () => {
        // matchMedia returns false for light scheme => defaults to dark
        window.matchMedia = vi.fn().mockReturnValue({ matches: false });

        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBe('dark');
    });

    it('defaults to light when system prefers light', () => {
        window.matchMedia = vi.fn().mockReturnValue({ matches: true });

        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBe('light');
    });

    it('reads saved theme from localStorage', () => {
        localStorage.setItem('vg_v1_theme', 'light');

        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBe('light');
    });

    it('toggles between light and dark themes', () => {
        localStorage.setItem('vg_v1_theme', 'dark');

        const { result } = renderHook(() => useTheme());
        expect(result.current.theme).toBe('dark');

        act(() => {
            result.current.toggleTheme();
        });
        expect(result.current.theme).toBe('light');

        act(() => {
            result.current.toggleTheme();
        });
        expect(result.current.theme).toBe('dark');
    });

    it('persists theme to localStorage on change', () => {
        localStorage.setItem('vg_v1_theme', 'dark');

        const { result } = renderHook(() => useTheme());

        act(() => {
            result.current.toggleTheme();
        });

        expect(localStorage.getItem('vg_v1_theme')).toBe('light');
    });

    it('applies data-theme attribute to document element', () => {
        localStorage.setItem('vg_v1_theme', 'dark');

        const { result } = renderHook(() => useTheme());
        expect(document.documentElement.getAttribute('data-theme')).toBe('dark');

        act(() => {
            result.current.toggleTheme();
        });
        expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });

    it('handles localStorage errors gracefully on read', () => {
        vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
            throw new Error('SecurityError');
        });
        window.matchMedia = vi.fn().mockReturnValue({ matches: false });

        const { result } = renderHook(() => useTheme());
        // Should fall back to system preference (dark)
        expect(result.current.theme).toBe('dark');
    });

    it('handles localStorage errors gracefully on write', () => {
        vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
            throw new Error('QuotaExceededError');
        });
        window.matchMedia = vi.fn().mockReturnValue({ matches: false });

        const { result } = renderHook(() => useTheme());

        // Should not throw
        act(() => {
            result.current.toggleTheme();
        });

        // Theme should still update in memory
        expect(result.current.theme).toBe('light');
    });

    it('provides a stable toggleTheme callback', () => {
        const { result, rerender } = renderHook(() => useTheme());
        const firstToggle = result.current.toggleTheme;

        rerender();
        expect(result.current.toggleTheme).toBe(firstToggle);
    });
});
