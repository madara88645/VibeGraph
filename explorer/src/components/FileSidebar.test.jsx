import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import FileSidebar from './FileSidebar';

describe('FileSidebar', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(
      new Error('dependency sidebar should not load shared graph data')
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows upload-first dependency guidance without requesting shared graph data', async () => {
    const user = userEvent.setup();

    render(
      <FileSidebar
        files={[]}
        selectedFile={null}
        onSelectFile={vi.fn()}
        nodeStats={{}}
        totalNodeCount={0}
        mobileOpen={false}
        fileDependencies={null}
      />
    );

    await user.click(screen.getByRole('tab', { name: /deps/i }));

    expect(
      screen.getByText('Dependency view appears after you upload and analyze a project.')
    ).toBeInTheDocument();
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });
});
