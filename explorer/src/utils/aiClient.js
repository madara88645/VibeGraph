const API_KEY_STORAGE_KEY = 'vg_v1_openrouter_key';
const MODEL_STORAGE_KEY = 'vg_v1_ai_model';

export const DEFAULT_AI_CONFIG = {
  provider: 'openrouter',
  defaultModel: 'deepseek/deepseek-v4-flash',
  allowedModels: [
    'deepseek/deepseek-v4-flash',
    'qwen/qwen3-coder-30b-a3b-instruct',
    'google/gemini-3.1-flash-lite',
    'anthropic/claude-sonnet-4.6',
    'meta-llama/llama-3.3-70b-instruct:free',
  ],
  requiresUserKey: true,
};

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
    requiresUserKey:
      typeof data.requiresUserKey === 'boolean'
        ? data.requiresUserKey
        : DEFAULT_AI_CONFIG.requiresUserKey,
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
    return await fetch(path, {
      ...options,
      signal: controller.signal,
    });
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
    throw new Error(detail);
  }

  return response.json();
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
