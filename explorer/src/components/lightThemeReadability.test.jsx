import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

vi.mock('reactflow', () => ({
  Handle: ({ type }) => <div data-testid={`${type}-handle`} />,
  Position: { Top: 'top', Bottom: 'bottom' },
}));

vi.mock('./CodeViewer', () => ({
  default: () => <div data-testid="code-viewer" />,
}));

import CustomNode from './CustomNode';
import ExplanationPanel from './ExplanationPanel';

describe('light theme readability regressions', () => {
  it('renders node text with theme variables instead of fixed dark-mode colors', () => {
    render(
      <CustomNode
        selected={false}
        data={{
          label: 'parse_project',
          file: 'app/routers/upload.py',
          lineno: 56,
          type: 'function',
        }}
      />
    );

    expect(screen.getByText('parse_project')).toHaveStyle('color: var(--text-primary)');
    expect(screen.getByText(/upload\.py/)).toHaveStyle('color: var(--text-secondary)');
    expect(screen.getByText('L56')).toHaveStyle('color: var(--text-muted)');
  });

  it('renders explanation copy with theme variables instead of fixed washed-out colors', () => {
    render(
      <ExplanationPanel
        node={{
          data: {
            label: 'parse_project',
            type: 'function',
            file: 'app/routers/upload.py',
            lineno: 56,
          },
        }}
        explanation={{
          explanation: {
            technical: 'Parses uploaded files.',
            analogy: 'Like sorting folders before study.',
            key_takeaway: 'Input gets normalized before analysis.',
          },
          snippet: 'def parse_project():\n    pass',
        }}
        loading={false}
        onClose={() => {}}
        fetchExplanation={() => {}}
      />
    );

    expect(screen.getByRole('tabpanel')).toHaveStyle('color: var(--text-secondary)');
    expect(screen.getByText(/Takeaway/i)).toHaveStyle('color: var(--text-primary)');
  });
});
