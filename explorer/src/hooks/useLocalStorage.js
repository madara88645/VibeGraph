import { useState, useCallback } from 'react';

const PREFIX = 'vg_v1_';

export function useLocalStorage(key, initialValue) {
    const prefixedKey = PREFIX + key;

    const [storedValue, setStoredValue] = useState(() => {
        try {
            const item = window.localStorage.getItem(prefixedKey);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            console.warn(`Error reading localStorage key "${prefixedKey}":`, error);
            return initialValue;
        }
    });

    const setValue = useCallback((value) => {
        try {
            const valueToStore = value instanceof Function ? value(storedValue) : value;
            setStoredValue(valueToStore);
            window.localStorage.setItem(prefixedKey, JSON.stringify(valueToStore));
        } catch (error) {
            console.warn(`Error setting localStorage key "${prefixedKey}":`, error);
        }
    }, [prefixedKey, storedValue]);

    const removeValue = useCallback(() => {
        try {
            window.localStorage.removeItem(prefixedKey);
            setStoredValue(initialValue);
        } catch (error) {
            console.warn(`Error removing localStorage key "${prefixedKey}":`, error);
        }
    }, [prefixedKey, initialValue]);

    return [storedValue, setValue, removeValue];
}

export function clearAllVibeGraphStorage() {
    try {
        const keys = Object.keys(window.localStorage).filter(k => k.startsWith(PREFIX));
        keys.forEach(k => window.localStorage.removeItem(k));
    } catch (error) {
        console.warn('Error clearing VibeGraph storage:', error);
    }
}
