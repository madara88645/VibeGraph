import { createElement } from 'react';
import { renderHook } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ToastContext, useToast } from './useToast';

describe('useToast', () => {
  it('throws when used outside a ToastProvider', () => {
    expect(() => renderHook(() => useToast())).toThrow(
      'useToast must be used within ToastProvider'
    );
  });

  it('returns the provided context value when used within a provider', () => {
    const value = { showToast: () => {} };
    const wrapper = ({ children }) =>
      createElement(ToastContext.Provider, { value }, children);

    const { result } = renderHook(() => useToast(), { wrapper });

    expect(result.current).toBe(value);
  });
});
