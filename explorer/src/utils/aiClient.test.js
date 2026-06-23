import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  buildAiHeaders,
  DEFAULT_AI_CONFIG,
  ensureAiReady,
  fetchAiConfig,
  fetchAiJson,
  fetchAiJsonWithRetry,
  fetchWithTimeout,
  getFriendlyAiErrorMessage,
  isRetryableAiError,
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

  it('returns the fallback for timeout abort errors', () => {
    const err = new DOMException('The operation was aborted.', 'AbortError');
    expect(getFriendlyAiErrorMessage(err, 'Timed out')).toBe('Timed out');
  });

  it('returns fallback for non-Error values', () => {
    expect(getFriendlyAiErrorMessage('string-err', 'Fallback')).toBe('Fallback');
    expect(getFriendlyAiErrorMessage(null, 'Fallback')).toBe('Fallback');
  });
});

describe('fetchWithTimeout', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('aborts a request after the timeout elapses', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((_path, options) => (
      new Promise((_resolve, reject) => {
        options.signal.addEventListener('abort', () => {
          reject(new DOMException('The operation was aborted.', 'AbortError'));
        });
      })
    ));

    const request = expect(fetchWithTimeout('/api/explain', {}, 50)).rejects.toThrow(/aborted/i);
    await vi.advanceTimersByTimeAsync(50);

    await request;
  });
});

// ─── fetchAiConfig ────────────────────────────────────────────────────
describe('DEFAULT_AI_CONFIG.allowedModels', () => {
  it('excludes the unreliable free Llama model', () => {
    expect(DEFAULT_AI_CONFIG.allowedModels).not.toContain(
      'meta-llama/llama-3.3-70b-instruct:free'
    );
  });

  it('keeps the curated models with a valid default', () => {
    expect(DEFAULT_AI_CONFIG.defaultModel).toBe('deepseek/deepseek-v4-flash');
    expect(DEFAULT_AI_CONFIG.allowedModels).toContain('deepseek/deepseek-v4-flash');
    expect(DEFAULT_AI_CONFIG.allowedModels).toContain('qwen/qwen3-coder-30b-a3b-instruct');
    expect(DEFAULT_AI_CONFIG.allowedModels).toContain('google/gemini-3.1-flash-lite');
    expect(DEFAULT_AI_CONFIG.allowedModels).toContain('anthropic/claude-sonnet-4.6');
    expect(DEFAULT_AI_CONFIG.allowedModels).toContain(DEFAULT_AI_CONFIG.defaultModel);
  });
});

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
          uploadLimits: {
            maxTotalBytes: 25 * 1024 * 1024,
            maxPerFileBytes: 1024 * 1024,
          },
        }),
    });

    const config = await fetchAiConfig();
    expect(config.provider).toBe('openrouter');
    expect(config.defaultModel).toBe('google/gemini-2.5-flash-lite');
    expect(config.allowedModels).toEqual(['google/gemini-2.5-flash-lite', 'openai/gpt-5-mini']);
    expect(config.requiresUserKey).toBe(false);
    expect(config.uploadLimits).toEqual({
      maxTotalBytes: 25 * 1024 * 1024,
      maxPerFileBytes: 1024 * 1024,
    });
  });

  it('falls back to DEFAULT_AI_CONFIG.allowedModels when server returns empty array', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ allowedModels: [] }),
    });

    const config = await fetchAiConfig();
    expect(config.allowedModels).toEqual(DEFAULT_AI_CONFIG.allowedModels);
    expect(config.uploadLimits).toEqual(DEFAULT_AI_CONFIG.uploadLimits);
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

describe('fetchAiJson error status', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('attaches the HTTP status to the thrown error (5xx with no JSON body)', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 503,
      json: () => Promise.reject(new Error('not json')),
    });

    await expect(
      fetchAiJson('/api/learning-path', { apiKey: '', body: {} }),
    ).rejects.toMatchObject({ status: 503, message: 'Request failed (503)' });
  });

  it('attaches the HTTP status to the thrown error (4xx with JSON detail)', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid API key' }),
    });

    await expect(
      fetchAiJson('/api/explain', { apiKey: 'bad', body: {} }),
    ).rejects.toMatchObject({ status: 401, message: 'Invalid API key' });
  });
});

describe('isRetryableAiError', () => {
  it('treats 502/503/504 gateway errors as retryable', () => {
    expect(isRetryableAiError({ status: 502 })).toBe(true);
    expect(isRetryableAiError({ status: 503 })).toBe(true);
    expect(isRetryableAiError({ status: 504 })).toBe(true);
  });

  it('treats 4xx client errors as non-retryable', () => {
    expect(isRetryableAiError({ status: 400 })).toBe(false);
    expect(isRetryableAiError({ status: 401 })).toBe(false);
    expect(isRetryableAiError({ status: 404 })).toBe(false);
  });

  it('treats a network error (no status) as retryable but an abort/timeout as not', () => {
    expect(isRetryableAiError(new TypeError('Failed to fetch'))).toBe(true);
    const abortError = Object.assign(new Error('aborted'), { name: 'AbortError' });
    expect(isRetryableAiError(abortError)).toBe(false);
  });
});

describe('fetchAiJsonWithRetry', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('retries a transient 503 and resolves once a later attempt succeeds', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({ ok: false, status: 503, json: () => Promise.reject(new Error('x')) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ steps: [] }) });

    const data = await fetchAiJsonWithRetry(
      '/api/learning-path',
      { apiKey: '', body: {} },
      { delaysMs: [0, 0] },
    );

    expect(data).toEqual({ steps: [] });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('gives up after exhausting the retry budget (3 attempts) and throws the last error', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 503,
      json: () => Promise.reject(new Error('x')),
    });

    await expect(
      fetchAiJsonWithRetry('/api/learning-path', { apiKey: '', body: {} }, { delaysMs: [0, 0] }),
    ).rejects.toMatchObject({ status: 503 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('does not retry a non-transient 4xx error', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Invalid API key' }),
    });

    await expect(
      fetchAiJsonWithRetry('/api/explain', { apiKey: 'bad', body: {} }, { delaysMs: [0, 0] }),
    ).rejects.toThrow('Invalid API key');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
