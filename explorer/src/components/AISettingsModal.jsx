import React, { useEffect, useMemo, useState, useRef } from 'react';

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
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  
  const [isRendered, setIsRendered] = useState(isOpen);
  const [isDismissed, setIsDismissed] = useState(!isOpen);

  useEffect(() => {
    if (isOpen) {
      Promise.resolve().then(() => {
        setIsRendered(true);
      });
      const timer = setTimeout(() => setIsDismissed(false), 20);
      return () => clearTimeout(timer);
    } else {
      Promise.resolve().then(() => {
        setIsDismissed(true);
      });
      const timer = setTimeout(() => setIsRendered(false), 300); // match transition
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const dropdownRef = useRef(null);
  const isClearDisabled = draftApiKey.length === 0;
  const clearButtonLabel = isClearDisabled ? 'Key is already clear' : 'Clear Key';


  const allowedModels = useMemo(() => {
    if (Array.isArray(apiConfig?.allowedModels) && apiConfig.allowedModels.length > 0) {
      return apiConfig.allowedModels;
    }
    return [];
  }, [apiConfig]);

  const supportedModelsLabel = useMemo(() => {
    if (!allowedModels.length) {
      return '';
    }
    return allowedModels.map(shortenModelName).join(', ');
  }, [allowedModels]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    const handleOutsideClick = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [isDropdownOpen]);

  if (!isRendered) {
    return null;
  }

  const handleSave = (event) => {
    if (event) event.preventDefault();
    onSave({ apiKey: draftApiKey, model: draftModel });
    onClose();
  };

  return (
    <div className={`ai-settings-overlay ${isDismissed ? 'dismissed' : ''}`} onClick={onClose}>
      <div
        className={`ai-settings-modal ${isDismissed ? 'dismissed' : ''}`}
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-settings-title"
      >
        <div className="ai-settings-header">
          <div>
            <h2 id="ai-settings-title">AI Settings</h2>
            <p className="ai-settings-subtitle">
              Your OpenRouter key stays in this browser session only.
            </p>
          </div>
          <button
            className="ai-settings-close"
            onClick={onClose}
            title="Close AI Settings"
            aria-label="Close AI Settings"
          >
            <span aria-hidden="true">x</span>
          </button>
        </div>

        <form onSubmit={handleSave}>
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
                aria-label={showKey ? 'Hide OpenRouter API Key' : 'Show OpenRouter API Key'}
                aria-pressed={showKey}
              >
                {showKey ? 'Hide' : 'Show'}
              </button>
            </div>
            <p className="ai-settings-help">
              {apiConfig?.requiresUserKey
                ? 'Production requires your own key.'
                : 'You can override the server key with your own key.'}
            </p>
          </div>

          <div className="ai-settings-field">
            <label id="ai-settings-model-label">Model</label>
            <div className="custom-dropdown-container" ref={dropdownRef}>
              <button
                type="button"
                className="custom-dropdown-trigger"
                onClick={() => setIsDropdownOpen((prev) => !prev)}
                aria-haspopup="listbox"
                aria-expanded={isDropdownOpen}
                aria-labelledby="ai-settings-model-label"
              >
                <span>{shortenModelName(draftModel)}</span>
                <span className="custom-dropdown-arrow">▼</span>
              </button>
              
              <ul
                className={`custom-dropdown-menu ${isDropdownOpen ? 'open' : ''}`}
                role="listbox"
              >
                {allowedModels.map((modelName) => (
                  <li
                    key={modelName}
                    role="option"
                    aria-selected={modelName === draftModel}
                    className={`custom-dropdown-item ${modelName === draftModel ? 'active' : ''}`}
                    onClick={() => {
                      onDraftModelChange(modelName);
                      setIsDropdownOpen(false);
                    }}
                  >
                    {shortenModelName(modelName)}
                  </li>
                ))}
              </ul>
            </div>
            <p className="ai-settings-help">
              Supported fast defaults only. Deprecated models like Grok fast are intentionally excluded.
            </p>
            {supportedModelsLabel ? (
              <p className="ai-settings-help">
                Supported now: {supportedModelsLabel}
              </p>
            ) : null}
          </div>
          </div>

          <div className="ai-settings-footer">
            <span style={{ display: 'inline-flex' }} title={clearButtonLabel}>
              <button
                type="button"
                className="ai-settings-secondary-btn"
                onClick={onClear}
                aria-label={clearButtonLabel}
                disabled={isClearDisabled}
              >
                Clear Key
              </button>
            </span>
            <button type="submit" className="ai-settings-primary-btn">
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default React.memo(AISettingsModal);
