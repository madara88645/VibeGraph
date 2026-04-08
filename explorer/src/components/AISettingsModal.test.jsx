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
          defaultModel: 'anthropic/claude-haiku-4.5',
          allowedModels: [
            'anthropic/claude-haiku-4.5',
            'google/gemini-2.5-flash-lite',
            'openai/gpt-5-mini',
            'deepseek/deepseek-chat-v3.1',
            'x-ai/grok-4.1-fast',
          ],
          requiresUserKey: true,
        }}
        draftApiKey=""
        draftModel="deepseek/deepseek-chat-v3.1"
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
    expect(screen.getByRole('option', { name: 'deepseek-chat-v3.1' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'grok-4.1-fast' })).toBeInTheDocument();
  });
});
