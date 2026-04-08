import React, { useMemo, useState } from 'react';

function shortenModelName(modelName) {
  return modelName.split('/').pop() || modelName;
}

const AISettingsModal = ({
  isOpen,
  onClose,
  apiConfig,
  draftApiKey,
  draftModel,
  configError,
  onSave,
  onClear,
  onDraftApiKeyChange,
  onDraftModelChange,
}) => {
  const [showKey, setShowKey] = useState(false);

  const allowedModels = useMemo(() => {
    if (Array.isArray(apiConfig?.allowedModels) && apiConfig.allowedModels.length > 0) {
      return apiConfig.allowedModels;
    }
    return [];
  }, [apiConfig]);

  if (!isOpen) {
    return null;
  }

  const handleSave = () => {
    onSave({
      apiKey: draftApiKey,
      model: draftModel || apiConfig?.defaultModel || allowedModels[0] || '',
    });
    onClose();
  };

  return (
    <div className="ai-settings-overlay" onClick={onClose}>
      <div
        className="ai-settings-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-settings-title"
      >
        <div className="ai-settings-header">
          <div>
            <h2 id="ai-settings-title">AI Settings</h2>
            <p className="ai-settings-subtitle">
              OpenRouter keyi sadece bu browser session&apos;inda tutulur.
            </p>
          </div>
          <button
            className="ai-settings-close"
            onClick={onClose}
            aria-label="Close AI Settings"
          >
            x
          </button>
        </div>

        <div className="ai-settings-body">
          <div className="ai-settings-meta">
            <span className="ai-settings-pill">
              Provider: {apiConfig?.provider || 'openrouter'}
            </span>
            <span className="ai-settings-pill">
              Default: {shortenModelName(apiConfig?.defaultModel || 'unknown')}
            </span>
          </div>

          {configError ? (
            <div className="ai-settings-alert ai-settings-alert-warning">{configError}</div>
          ) : null}

          <div className="ai-settings-field">
            <label htmlFor="ai-settings-key">OpenRouter API Key</label>
            <div className="ai-settings-key-row">
              <input
                id="ai-settings-key"
                type={showKey ? 'text' : 'password'}
                value={draftApiKey}
                onChange={(event) => onDraftApiKeyChange(event.target.value)}
                placeholder="sk-or-v1-..."
                autoComplete="off"
                spellCheck="false"
              />
              <button
                type="button"
                className="ai-settings-secondary-btn"
                onClick={() => setShowKey((prev) => !prev)}
              >
                {showKey ? 'Hide' : 'Show'}
              </button>
            </div>
            <p className="ai-settings-help">
              {apiConfig?.requiresUserKey
                ? 'Production modunda kendi anahtarin gerekli.'
                : 'Istersen kendi anahtarinla override edebilirsin.'}
            </p>
          </div>

          <div className="ai-settings-field">
            <label htmlFor="ai-settings-model">Model</label>
            <select
              id="ai-settings-model"
              value={draftModel}
              onChange={(event) => onDraftModelChange(event.target.value)}
            >
              {allowedModels.map((modelName) => (
                <option key={modelName} value={modelName}>
                  {shortenModelName(modelName)}
                </option>
              ))}
            </select>
            <p className="ai-settings-help">
              Hafif ve guvenli bir model listesi tutuluyor; deploy sonrasi surprise cost istemiyoruz.
            </p>
          </div>
        </div>

        <div className="ai-settings-footer">
          <button
            type="button"
            className="ai-settings-secondary-btn"
            onClick={onClear}
          >
            Clear Key
          </button>
          <button type="button" className="ai-settings-primary-btn" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default React.memo(AISettingsModal);
