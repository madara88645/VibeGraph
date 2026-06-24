const API_KEY_STORAGE_KEY = 'vg_v1_openrouter_key';
const MODEL_STORAGE_KEY = 'vg_v1_ai_model';
const DEFAULT_UPLOAD_LIMITS = {
  maxTotalBytes: 25 * 1024 * 1024,
  maxPerFileBytes: 1024 * 1024,
};

export const DEFAULT_AI_CONFIG = {
  provider: 'openrouter',
  defaultModel: 'deepseek/deepseek-v4-flash',
  allowedModels: [
    'deepseek/deepseek-v4-flash',
    'qwen/qwen3-coder-30b-a3b-instruct',
    'google/gemini-3.1-flash-lite',
    'anthropic/claude-sonnet-4.6',
  ],
  requiresUserKey: true,
  trialEnabled: false,
  trialRemaining: 0,
  uploadLimits: DEFAULT_UPLOAD_LIMITS,
};

export const TRIAL_REMAINING_EVENT = 'vibegraph:trial-remaining';
export const TRIAL_EXHAUSTED_EVENT = 'vibegraph:trial-exhausted';

const TRIAL_EXHAUSTED_MESSAGE =
  'Free trial used up — add your own OpenRouter key in AI Settings.';

function normalizePositiveNumber(value, fallback) {
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function normalizeNonNegativeNumber(value, fallback = 0) {
  return Number.isFinite(value) && value >= 0 ? value : fallback;
}

function publishTrialResponse(response) {
  const rawRemaining = response?.headers?.get?.('X-Trial-Remaining');
  if (rawRemaining !== null && rawRemaining !== undefined) {
    const remaining = normalizeNonNegativeNumber(Number(rawRemaining));
    window.dispatchEvent(
      new CustomEvent(TRIAL_REMAINING_EVENT, { detail: { remaining } }),
    );
  }

  if (response?.status === 402) {
    window.dispatchEvent(
      new CustomEvent(TRIAL_EXHAUSTED_EVENT, {
        detail: { message: TRIAL_EXHAUSTED_MESSAGE },
      }),
    );
  }
}

function normalizeUploadLimits(uploadLimits) {
  return {
    maxTotalBytes: normalizePositiveNumber(
      Number(uploadLimits?.maxTotalBytes),
      DEFAULT_UPLOAD_LIMITS.maxTotalBytes,
    ),
    maxPerFileBytes: normalizePositiveNumber(
      Number(uploadLimits?.maxPerFileBytes),
      DEFAULT_UPLOAD_LIMITS.maxPerFileBytes,
    ),
  };
}

export function getStoredApiKey() {
  try {
    return window.sessionStorage.getItem(API_KEY_STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

export function setStoredApiKey(value) {
  try {
    const nextValue = value.trim();
    if (nextValue) {
      window.sessionStorage.setItem(API_KEY_STORAGE_KEY, nextValue);
    } else {
      window.sessionStorage.removeItem(API_KEY_STORAGE_KEY);
    }
  } catch {
    // Ignore storage issues in private/incognito contexts.
  }
}

export function getStoredModel() {
  try {
    return window.localStorage.getItem(MODEL_STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

export function setStoredModel(value) {
  try {
    const nextValue = value.trim();
    if (nextValue) {
      window.localStorage.setItem(MODEL_STORAGE_KEY, nextValue);
    } else {
      window.localStorage.removeItem(MODEL_STORAGE_KEY);
    }
  } catch {
    // Ignore storage issues in private/incognito contexts.
  }
}

export async function fetchAiConfig() {
  const response = await fetch('/api/ai-config');
  if (!response.ok) {
    throw new Error(`AI config request failed (${response.status})`);
  }

  const data = await response.json();
  const allowedModels = Array.isArray(data.allowedModels) && data.allowedModels.length > 0
    ? data.allowedModels
    : DEFAULT_AI_CONFIG.allowedModels;

  return {
    provider: data.provider || DEFAULT_AI_CONFIG.provider,
    defaultModel: data.defaultModel || allowedModels[0] || DEFAULT_AI_CONFIG.defaultModel,
    allowedModels,
    uploadLimits: normalizeUploadLimits(data.uploadLimits),
    requiresUserKey:
      typeof data.requiresUserKey === 'boolean'
        ? data.requiresUserKey
        : DEFAULT_AI_CONFIG.requiresUserKey,
    trialEnabled:
      typeof data.trialEnabled === 'boolean'
        ? data.trialEnabled
        : DEFAULT_AI_CONFIG.trialEnabled,
    trialRemaining: normalizeNonNegativeNumber(
      Number(data.trialRemaining),
      DEFAULT_AI_CONFIG.trialRemaining,
    ),
  };
}

export function buildAiHeaders(apiKey, { includeContentType = true } = {}) {
  const headers = {};
  if (includeContentType) {
    headers['Content-Type'] = 'application/json';
  }
  if (apiKey?.trim()) {
    headers.Authorization = `Bearer ${apiKey.trim()}`;
  }
  return headers;
}

export function ensureAiReady(aiReady, onRequireAiKey, message) {
  if (aiReady) {
    return true;
  }
  onRequireAiKey?.(message || 'Open AI Settings and add your OpenRouter API key.');
  return false;
}

export async function fetchWithTimeout(path, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(path, {
      ...options,
      signal: controller.signal,
    });
    publishTrialResponse(response);
    return response;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function fetchAiJson(path, { apiKey, method = 'POST', body, timeoutMs } = {}) {
  const response = await fetchWithTimeout(path, {
    method,
    headers: buildAiHeaders(apiKey),
    body: body ? JSON.stringify(body) : undefined,
  }, timeoutMs);

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.message || payload.error || detail;
    } catch {
      // Ignore JSON parsing failures and keep the HTTP fallback message.
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

// Gateway/proxy statuses that signal a transient backend hiccup (e.g. a Fly.io
// cold start) worth retrying. Client (4xx) errors are deliberately excluded —
// retrying an invalid API key or a bad request just wastes time and money.
const TRANSIENT_HTTP_STATUSES = new Set([502, 503, 504]);

export function isRetryableAiError(error) {
  if (!error) {
    return false;
  }
  const { status } = error;
  if (status === undefined || status === null) {
    // No HTTP status means the request never completed. A plain network
    // failure is worth retrying; an abort/timeout is not — retrying would only
    // compound an already-long wait.
    return error.name !== 'AbortError';
  }
  return TRANSIENT_HTTP_STATUSES.has(status);
}

// Wraps fetchAiJson with bounded, backed-off retries for transient failures.
// Opt-in: callers that should NOT retry (explain, chat) keep using fetchAiJson
// directly, so this keeps the blast radius to the caller that needs it.
export async function fetchAiJsonWithRetry(
  path,
  options = {},
  { retries = 2, delaysMs = [1000, 2000], isRetryable = isRetryableAiError } = {},
) {
  let lastError;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await fetchAiJson(path, options);
    } catch (error) {
      lastError = error;
      if (attempt === retries || !isRetryable(error)) {
        throw error;
      }
      const delay = delaysMs[Math.min(attempt, delaysMs.length - 1)] ?? 0;
      if (delay > 0) {
        await new Promise((resolve) => window.setTimeout(resolve, delay));
      }
    }
  }
  // The loop always returns or throws; this satisfies control-flow analysis.
  throw lastError;
}

export function getFriendlyAiErrorMessage(error, fallbackMessage) {
  if (error instanceof Error && error.message) {
    const loweredMessage = error.message.toLowerCase();
    if (
      error.name === 'AbortError' ||
      loweredMessage === 'network error' ||
      loweredMessage.includes('failed to fetch') ||
      loweredMessage.includes('load failed')
    ) {
      return fallbackMessage;
    }
    return error.message;
  }
  return fallbackMessage;
}
