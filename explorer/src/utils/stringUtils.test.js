import { describe, expect, it } from 'vitest';

import { getShortName } from './stringUtils';

describe('getShortName', () => {
  it('returns an empty string for empty input', () => {
    expect(getShortName('')).toBe('');
  });

  it('returns an empty string for null input', () => {
    expect(getShortName(null)).toBe('');
  });

  it('returns an empty string for undefined input', () => {
    expect(getShortName(undefined)).toBe('');
  });

  it('returns the whole string when there is no separator', () => {
    expect(getShortName('file.py')).toBe('file.py');
  });

  it('returns the basename for a forward-slash path', () => {
    expect(getShortName('src/utils/file.py')).toBe('file.py');
  });

  it('returns an empty string for a trailing forward slash', () => {
    expect(getShortName('src/utils/')).toBe('');
  });

  it('returns the basename for a Windows-style backslash path', () => {
    expect(getShortName('src\\utils\\file.py')).toBe('file.py');
  });

  it('uses the last separator when the path mixes slash styles', () => {
    expect(getShortName('src/utils\\file.py')).toBe('file.py');
    expect(getShortName('src\\utils/file.py')).toBe('file.py');
  });
});
