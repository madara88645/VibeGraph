import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('react-markdown', () => ({
  default: ({ children }) => <div data-testid="markdown">{children}</div>,
}));

vi.mock('./CodeViewer', () => ({
  default: () => <div data-testid="code-viewer" />,
}));

import ExplanationPanel from './ExplanationPanel';

const MOCK_NODE = {
  id: 'parse_project',
  data: {
    label: 'parse_project',
    type: 'function',
    file: 'app/routers/upload.py',
    lineno: 56,
  },
};

const STRUCTURED_EXPLANATION = {
  explanation: {
    technical: 'Technical explanation body',
    analogy: 'Analogy explanation body',
    key_takeaway: 'Normalize paths before analysis.',
  },
  snippet: 'def parse_project():\n    pass',
};

function renderPanel(props = {}) {
  const defaults = {
    node: MOCK_NODE,
    explanation: null,
    loading: false,
    onClose: vi.fn(),
    fetchExplanation: vi.fn(),
  };
  return render(<ExplanationPanel {...defaults} {...props} />);
}

describe('ExplanationPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('closes on Escape key press', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderPanel({ onClose });

    // Ensure the panel is rendered by waiting for something
    await screen.findByRole('tab', { name: /Technical/i });

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls fetchExplanation on mount with default tab and level', () => {
    const fetchExplanation = vi.fn();
    renderPanel({ fetchExplanation });

    expect(fetchExplanation).toHaveBeenCalledTimes(1);
    expect(fetchExplanation).toHaveBeenCalledWith(
      MOCK_NODE,
      'technical',
      'intermediate'
    );
  });

  it('refetches when the Analogy tab is selected', async () => {
    const user = userEvent.setup();
    const fetchExplanation = vi.fn();
    renderPanel({ fetchExplanation });

    await user.click(screen.getByRole('tab', { name: /Analogy/i }));

    expect(fetchExplanation).toHaveBeenCalledTimes(2);
    expect(fetchExplanation).toHaveBeenLastCalledWith(
      MOCK_NODE,
      'analogy',
      'intermediate'
    );
  });

  it('refetches when the difficulty level changes', async () => {
    const user = userEvent.setup();
    const fetchExplanation = vi.fn();
    renderPanel({ fetchExplanation });

    await user.click(screen.getByRole('button', { name: 'Set difficulty level to beginner' }));

    expect(fetchExplanation).toHaveBeenCalledTimes(2);
    expect(fetchExplanation).toHaveBeenLastCalledWith(
      MOCK_NODE,
      'technical',
      'beginner'
    );
  });

  it('shows loading UI while explanation is loading', () => {
    renderPanel({ loading: true });
    expect(screen.getByText('AI is thinking...')).toBeInTheDocument();
  });

  it('shows a formatting error as such, not as an invalid API key', () => {
    // The raw AI response contains the word "key" (e.g. "key_takeaway"), which
    // previously misclassified parse failures as an invalid API key.
    renderPanel({
      explanation: {
        explanation: {
          is_error: true,
          analogy: 'AI Formatting Error',
          technical:
            'The AI did not return a valid JSON object. Raw AI Response: "key_takeaway": ...',
          key_takeaway: 'AI output format mismatch.',
        },
        snippet: 'def foo():\n    pass',
      },
      fetchExplanation: vi.fn(),
    });

    expect(screen.getByText('AI Formatting Error')).toBeInTheDocument();
    expect(screen.queryByText('Invalid API Key')).not.toBeInTheDocument();
  });

  it('renders analogy content on the Analogy tab, not technical copy', async () => {
    const user = userEvent.setup();
    renderPanel({
      explanation: STRUCTURED_EXPLANATION,
      fetchExplanation: vi.fn(),
    });

    expect(screen.getByText('Technical explanation body')).toBeInTheDocument();

    await user.click(screen.getByRole('tab', { name: /Analogy/i }));

    expect(screen.getByText('Analogy explanation body')).toBeInTheDocument();
    expect(screen.queryByText('Technical explanation body')).not.toBeInTheDocument();
  });
});
