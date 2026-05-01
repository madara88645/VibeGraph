import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  buildAiHeaders,
  DEFAULT_AI_CONFIG,
  ensureAiReady,
  fetchAiConfig,
  fetchAiJson,
  getFriendlyAiErrorMessage,
  getStoredApiKey,
  getStoredModel,
  setStoredApiKey,
  setStoredModel,
} from './aiClient';

// ─── Storage helpers ──────────────────────────────────────────────────
describe('getStoredApiKey / setStoredApiKey', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('returns empty string when nothing is stored', () => {
    expect(getStoredApiKey()).toBe('');
  });

  it('round-trips a trimmed key through sessionStorage', () => {
    setStoredApiKey('  sk-abc123  ');
    expect(getStoredApiKey()).toBe('sk-abc123');
    expect(sessionStorage.getItem('vg_v1_openrouter_key')).toBe('sk-abc123');
  });

  it('removes the key when set to an empty/whitespace string', () => {
    setStoredApiKey('sk-abc123');
    expect(getStoredApiKey()).toBe('sk-abc123');

    setStoredApiKey('   ');
    expect(getStoredApiKey()).toBe('');
    expect(sessionStorage.getItem('vg_v1_openrouter_key')).toBeNull();
  });
});

describe('getStoredModel / setStoredModel', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('returns empty string when nothing is stored', () => {
    expect(getStoredModel()).toBe('');
  });

  it('round-trips a trimmed model name through localStorage', () => {
    setStoredModel('  openai/gpt-5-mini  ');
    expect(getStoredModel()).toBe('openai/gpt-5-mini');
  });

  it('removes the model when set to an empty string', () => {
    setStoredModel('openai/gpt-5-mini');
    setStoredModel('');
    expect(getStoredModel()).toBe('');
    expect(localStorage.getItem('vg_v1_ai_model')).toBeNull();
  });
});

// ─── buildAiHeaders ───────────────────────────────────────────────────
describe('buildAiHeaders', () => {
  it('includes Content-Type by default', () => {
    const headers = buildAiHeaders('sk-key');
    expect(headers['Content-Type']).toBe('application/json');
  });

  it('omits Content-Type when includeContentType is false', () => {
    const headers = buildAiHeaders('sk-key', { includeContentType: false });
    expect(headers['Content-Type']).toBeUndefined();
  });

  it('adds Authorization header with trimmed key', () => {
    const headers = buildAiHeaders('  sk-key  ');
    expect(headers.Authorization).toBe('Bearer sk-key');
  });

  it('omits Authorization when key is empty', () => {
    const headers = buildAiHeaders('');
    expect(headers.Authorization).toBeUndefined();
  });

  it('omits Authorization when key is null/undefined', () => {
    expect(buildAiHeaders(null).Authorization).toBeUndefined();
    expect(buildAiHeaders(undefined).Authorization).toBeUndefined();
  });
});

// ─── ensureAiReady ────────────────────────────────────────────────────
describe('ensureAiReady', () => {
  it('returns true and does NOT call onRequireAiKey when AI is ready', () => {
    const onRequire = vi.fn();
    expect(ensureAiReady(true, onRequire, 'Add key')).toBe(true);
    expect(onRequire).not.toHaveBeenCalled();
  });

  it('returns false and calls onRequireAiKey when AI is NOT ready', () => {
    const onRequire = vi.fn();
    expect(ensureAiReady(false, onRequire, 'Add key')).toBe(false);
    expect(onRequire).toHaveBeenCalledWith('Add key');
  });

  it('uses fallback message when none is provided', () => {
    const onRequire = vi.fn();
    ensureAiReady(false, onRequire);
    expect(onRequire).toHaveBeenCalledWith(
      'Open AI Settings and add your OpenRouter API key.',
    );
  });
});

// ─── getFriendlyAiErrorMessage ────────────────────────────────────────
describe('getFriendlyAiErrorMessage', () => {
  it('returns the fallback for "Failed to fetch" network errors', () => {
    const err = new Error('Failed to fetch');
    expect(getFriendlyAiErrorMessage(err, 'Offline')).toBe('Offline');
  });

  it('returns the fallback for "Load failed" Safari-style errors', () => {
    const err = new Error('Load failed');
    expect(getFriendlyAiErrorMessage(err, 'Offline')).toBe('Offline');
  });

  it('returns the fallback for "network error" (case-insensitive)', () => {
    const err = new Error('Network Error');
    expect(getFriendlyAiErrorMessage(err, 'Offline')).toBe('Offline');
  });

  it('passes through non-network error messages', () => {
    const err = new Error('Invalid API key');
    expect(getFriendlyAiErrorMessage(err, 'Offline')).toBe('Invalid API key');
  });

  it('returns fallback for non-Error values', () => {
    expect(getFriendlyAiErrorMessage('string-err', 'Fallback')).toBe('Fallback');
    expect(getFriendlyAiErrorMessage(null, 'Fallback')).toBe('Fallback');
  });
});

// ─── fetchAiConfig ────────────────────────────────────────────────────
describe('fetchAiConfig', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns server config with allowedModels when response is valid', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          provider: 'openrouter',
          defaultModel: 'google/gemini-2.5-flash-lite',
          allowedModels: ['google/gemini-2.5-flash-lite', 'openai/gpt-5-mini'],
          requiresUserKey: false,
        }),
    });

    const config = await fetchAiConfig();
    expect(config.provider).toBe('openrouter');
    expect(config.defaultModel).toBe('google/gemini-2.5-flash-lite');
    expect(config.allowedModels).toEqual(['google/gemini-2.5-flash-lite', 'openai/gpt-5-mini']);
    expect(config.requiresUserKey).toBe(false);
  });

  it('falls back to DEFAULT_AI_CONFIG.allowedModels when server returns empty array', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ allowedModels: [] }),
    });

    const config = await fetchAiConfig();
    expect(config.allowedModels).toEqual(DEFAULT_AI_CONFIG.allowedModels);
  });

  it('throws when response is not ok', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 500,
    });

    await expect(fetchAiConfig()).rejects.toThrow('AI config request failed (500)');
  });
});

// ─── fetchAiJson ──────────────────────────────────────────────────────
describe('fetchAiJson', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns parsed JSON on success', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ answer: 'Hello' }),
    });

    const data = await fetchAiJson('/api/chat', {
      apiKey: 'sk-test',
      body: { question: 'Hi' },
    });
    expect(data).toEqual({ answer: 'Hello' });

    // Verify correct headers were sent
    const [, options] = globalThis.fetch.mock.calls[0];
    expect(options.headers.Authorization).toBe('Bearer sk-test');
    expect(options.headers['Content-Type']).toBe('application/json');
  });

  it('throws with server detail on error response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid API key' }),
    });

    await expect(
      fetchAiJson('/api/explain', { apiKey: 'bad-key', body: {} }),
    ).rejects.toThrow('Invalid API key');
  });

  it('throws generic message when error response has no JSON body', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 503,
      json: () => Promise.reject(new Error('not json')),
    });

    await expect(
      fetchAiJson('/api/chat', { apiKey: 'sk-test', body: {} }),
    ).rejects.toThrow('Request failed (503)');
  });

  it('uses GET when method is overridden', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'ok' }),
    });

    await fetchAiJson('/api/health', { apiKey: '', method: 'GET' });

    const [, options] = globalThis.fetch.mock.calls[0];
    expect(options.method).toBe('GET');
    expect(options.body).toBeUndefined();
  });
});
