import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage, clearAllVibeGraphStorage } from './useLocalStorage';

describe('useLocalStorage', () => {
    beforeEach(() => {
        localStorage.clear();
        vi.restoreAllMocks();
    });

    it('returns default value when localStorage is empty', () => {
        const { result } = renderHook(() => useLocalStorage('testKey', 'default'));
        expect(result.current[0]).toBe('default');
    });

    it('reads existing value from localStorage', () => {
        localStorage.setItem('vg_v1_myKey', JSON.stringify('saved-value'));
        const { result } = renderHook(() => useLocalStorage('myKey', 'default'));
        expect(result.current[0]).toBe('saved-value');
    });

    it('reads existing object value from localStorage', () => {
        const obj = { theme: 'dark', zoom: 1.5 };
        localStorage.setItem('vg_v1_settings', JSON.stringify(obj));
        const { result } = renderHook(() => useLocalStorage('settings', {}));
        expect(result.current[0]).toEqual(obj);
    });

    it('updates localStorage when setValue is called', () => {
        const { result } = renderHook(() => useLocalStorage('counter', 0));

        act(() => {
            result.current[1](42);
        });

        expect(result.current[0]).toBe(42);
        expect(JSON.parse(localStorage.getItem('vg_v1_counter'))).toBe(42);
    });

    it('supports functional updates', () => {
        const { result } = renderHook(() => useLocalStorage('counter', 10));

        act(() => {
            result.current[1]((prev) => prev + 5);
        });

        expect(result.current[0]).toBe(15);
        expect(JSON.parse(localStorage.getItem('vg_v1_counter'))).toBe(15);
    });

    it('handles localStorage read errors gracefully', () => {
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
        vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
            throw new Error('SecurityError');
        });

        const { result } = renderHook(() => useLocalStorage('broken', 'fallback'));
        expect(result.current[0]).toBe('fallback');
        expect(warnSpy).toHaveBeenCalled();

        warnSpy.mockRestore();
    });

    it('handles localStorage write errors gracefully (e.g., quota exceeded)', () => {
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
        vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
            throw new DOMException('QuotaExceededError');
        });

        const { result } = renderHook(() => useLocalStorage('big', 'initial'));

        act(() => {
            result.current[1]('new-value');
        });

        // The state should still update in memory even if persistence fails
        expect(warnSpy).toHaveBeenCalled();
        warnSpy.mockRestore();
    });

    it('removeValue resets to initial value and removes from localStorage', () => {
        localStorage.setItem('vg_v1_removable', JSON.stringify('stored'));
        const { result } = renderHook(() => useLocalStorage('removable', 'default'));

        expect(result.current[0]).toBe('stored');

        act(() => {
            result.current[2](); // removeValue
        });

        expect(result.current[0]).toBe('default');
        expect(localStorage.getItem('vg_v1_removable')).toBeNull();
    });

    it('prefixes keys with vg_v1_', () => {
        const { result } = renderHook(() => useLocalStorage('myPrefixed', 'val'));

        act(() => {
            result.current[1]('updated');
        });

        expect(localStorage.getItem('vg_v1_myPrefixed')).toBe('"updated"');
        expect(localStorage.getItem('myPrefixed')).toBeNull();
    });
});

describe('clearAllVibeGraphStorage', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it('removes all vg_v1_ prefixed keys', () => {
        localStorage.setItem('vg_v1_theme', '"dark"');
        localStorage.setItem('vg_v1_zoom', '1.5');
        localStorage.setItem('other_key', 'keep');

        clearAllVibeGraphStorage();

        expect(localStorage.getItem('vg_v1_theme')).toBeNull();
        expect(localStorage.getItem('vg_v1_zoom')).toBeNull();
        expect(localStorage.getItem('other_key')).toBe('keep');
    });

    it('handles errors gracefully', () => {
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
        // Make localStorage throw when accessed
        vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
            throw new Error('Access denied');
        });

        localStorage.setItem('vg_v1_broken', '"val"');

        expect(() => clearAllVibeGraphStorage()).not.toThrow();
        expect(warnSpy).toHaveBeenCalled();

        warnSpy.mockRestore();
    });
});
