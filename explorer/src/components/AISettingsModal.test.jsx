import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import AISettingsModal from './AISettingsModal';

describe('AISettingsModal', () => {
  it('renders ASCII-only guidance and lower-cost model options', () => {
    render(
      <AISettingsModal
        isOpen
        onClose={vi.fn()}
        apiConfig={{
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
        }}
        draftApiKey=""
        draftModel="qwen/qwen3-coder-30b-a3b-instruct"
        configError=""
        onSave={vi.fn()}
        onClear={vi.fn()}
        onDraftApiKeyChange={vi.fn()}
        onDraftModelChange={vi.fn()}
      />
    );

    expect(
      screen.getByText('Your OpenRouter key stays in this browser session only.')
    ).toBeInTheDocument();
    expect(screen.getByText('Production requires your own key.')).toBeInTheDocument();
    expect(
      screen.getByText('Lean model list: fast defaults plus lower-cost backup options.')
    ).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'qwen3-coder-30b-a3b-instruct' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'deepseek-v4-flash' })).toBeInTheDocument();
  });

  it('disables Clear Key and explains why when the draft key is empty', () => {
    render(
      <AISettingsModal
        isOpen
        onClose={vi.fn()}
        apiConfig={{
          provider: 'openrouter',
          defaultModel: 'deepseek/deepseek-v4-flash',
          allowedModels: ['deepseek/deepseek-v4-flash'],
          requiresUserKey: true,
        }}
        draftApiKey=""
        draftModel="deepseek/deepseek-v4-flash"
        configError=""
        onSave={vi.fn()}
        onClear={vi.fn()}
        onDraftApiKeyChange={vi.fn()}
        onDraftModelChange={vi.fn()}
      />
    );

    const clearKeyButton = screen.getByRole('button', { name: 'Key is already clear' });
    expect(clearKeyButton).toBeDisabled();
    expect(clearKeyButton.closest('span')).toHaveAttribute('title', 'Key is already clear');
  });
});
