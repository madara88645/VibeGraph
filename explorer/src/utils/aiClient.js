const API_KEY_STORAGE_KEY = 'vg_v1_openrouter_key';
const MODEL_STORAGE_KEY = 'vg_v1_ai_model';

export const DEFAULT_AI_CONFIG = {
  provider: 'openrouter',
  defaultModel: 'anthropic/claude-haiku-4.5',
  allowedModels: [
    'anthropic/claude-haiku-4.5',
    'google/gemini-2.5-flash-lite',
    'openai/gpt-5-mini',
    'deepseek/deepseek-chat-v3.1',
    'x-ai/grok-4.1-fast',
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

export async function fetchAiJson(path, { apiKey, method = 'POST', body }) {
  const response = await fetch(path, {
    method,
    headers: buildAiHeaders(apiKey),
    body: body ? JSON.stringify(body) : undefined,
  });

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
