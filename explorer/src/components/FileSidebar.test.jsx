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

  it('correctly populates and displays "used by" dependencies in the Deps tab', async () => {
    const user = userEvent.setup();
    const files = ['src/main.py', 'src/utils.py'];
    const fileDependencies = [
      {
        source_file: 'src/main.py',
        target_file: 'src/utils.py',
        imports: ['helper_func'],
      },
    ];
    const onSelectFile = vi.fn();

    render(
      <FileSidebar
        files={files}
        selectedFile={null}
        onSelectFile={onSelectFile}
        nodeStats={{}}
        totalNodeCount={2}
        mobileOpen={false}
        fileDependencies={fileDependencies}
      />
    );

    await user.click(screen.getByRole('tab', { name: /deps/i }));

    expect(screen.getAllByText('main.py').length).toBe(2);
    expect(screen.getAllByText('utils.py').length).toBe(2);
    expect(screen.getByText('→ imports')).toBeInTheDocument();
    expect(screen.getByText('← used by')).toBeInTheDocument();

    const usedByButton = screen.getAllByRole('button', { name: 'src/main.py' }).find(
      (btn) => btn.className.includes('deps-item-clickable')
    );
    expect(usedByButton).toBeInTheDocument();
    await user.click(usedByButton);
    expect(onSelectFile).toHaveBeenCalledWith('src/main.py');
  });
});
