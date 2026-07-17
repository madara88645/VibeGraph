import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the heavy syntax highlighter so tests focus on interactive logic,
// not token rendering (mirrors CodePanel.test.jsx). CodeViewer pulls in the
// `vscDarkPlus` theme, so stub that export specifically.
vi.mock('react-syntax-highlighter', () => ({
    Prism: ({ children }) => <pre data-testid="syntax-highlighter">{children}</pre>,
}));
vi.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
    vscDarkPlus: {},
}));

import CodeViewer from './CodeViewer';

const SAMPLE_CODE = "def main():\n    return 42";

describe('CodeViewer', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the inline Source Code Preview when code is a non-empty string', () => {
        render(<CodeViewer code={SAMPLE_CODE} />);

        expect(screen.getByText('Source Code Preview')).toBeInTheDocument();
        expect(screen.getByLabelText('Expand code')).toBeInTheDocument();
        // No fullscreen dialog until the user expands.
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('renders nothing when code is an empty string', () => {
        const { container } = render(<CodeViewer code="" />);

        expect(container).toBeEmptyDOMElement();
        expect(screen.queryByText('Source Code Preview')).not.toBeInTheDocument();
    });

    it('renders nothing when code is undefined', () => {
        const { container } = render(<CodeViewer />);

        expect(container).toBeEmptyDOMElement();
        expect(screen.queryByLabelText('Expand code')).not.toBeInTheDocument();
    });

    it('opens the fullscreen overlay dialog when the expand button is clicked', async () => {
        const user = userEvent.setup();
        render(<CodeViewer code={SAMPLE_CODE} />);

        await user.click(screen.getByLabelText('Expand code'));

        // The overlay renders through a portal to document.body, so query the
        // whole screen rather than the render container.
        const dialog = screen.getByRole('dialog');
        expect(dialog).toBeInTheDocument();
        expect(document.body).toContainElement(dialog);
        expect(screen.getByLabelText('Exit fullscreen (Press Esc)')).toBeInTheDocument();
    });

    it('closes the dialog when Escape is pressed while fullscreen', async () => {
        const user = userEvent.setup();
        render(<CodeViewer code={SAMPLE_CODE} />);

        await user.click(screen.getByLabelText('Expand code'));
        expect(screen.getByRole('dialog')).toBeInTheDocument();

        await user.keyboard('{Escape}');

        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('ignores Escape when not fullscreen', async () => {
        const user = userEvent.setup();
        render(<CodeViewer code={SAMPLE_CODE} />);

        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

        await user.keyboard('{Escape}');

        // Nothing opened or broke; the inline preview is still intact.
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
        expect(screen.getByText('Source Code Preview')).toBeInTheDocument();
    });

    it('closes the dialog when the overlay backdrop is clicked', async () => {
        const user = userEvent.setup();
        render(<CodeViewer code={SAMPLE_CODE} />);

        await user.click(screen.getByLabelText('Expand code'));
        const dialog = screen.getByRole('dialog');
        // The backdrop is the overlay wrapping the dialog.
        const overlay = dialog.parentElement;

        await user.click(overlay);

        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('keeps the dialog open when clicking inside it (stopPropagation)', async () => {
        const user = userEvent.setup();
        render(<CodeViewer code={SAMPLE_CODE} />);

        await user.click(screen.getByLabelText('Expand code'));
        const dialog = screen.getByRole('dialog');

        await user.click(dialog);

        expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
});
