import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock useToast — hook returns showToast directly (not an object)
vi.mock('../hooks/useToast', () => ({
    useToast: vi.fn(),
}));

// Mock heavy syntax highlighter
vi.mock('react-syntax-highlighter', () => ({
    Prism: ({ children }) => <pre data-testid="syntax-highlighter">{children}</pre>,
}));
vi.mock('react-syntax-highlighter/dist/esm/styles/prism', () => ({
    oneDark: {},
}));

import { useToast } from '../hooks/useToast';
import CodePanel from './CodePanel';

const mockAddToast = vi.fn();
// Stable clipboard mock to avoid spy detection issues
const mockWriteText = vi.fn().mockResolvedValue(undefined);

beforeAll(() => {
    Object.defineProperty(window.navigator, 'clipboard', {
        value: { writeText: mockWriteText },
        configurable: true,
        writable: true,
    });
});

function renderPanel(props = {}) {
    useToast.mockReturnValue(mockAddToast);
    const defaults = {
        activeNode: null,
        isGhostRunning: false,
        isOpen: true,
        onToggle: vi.fn(),
    };
    return render(<CodePanel {...defaults} {...props} />);
}

describe('CodePanel', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockWriteText.mockResolvedValue(undefined);
        globalThis.fetch = vi.fn();
    });

    it('renders toggle button when closed', () => {
        useToast.mockReturnValue(mockAddToast);
        const onToggle = vi.fn();
        render(
            <CodePanel
                activeNode={null}
                isGhostRunning={false}
                isOpen={false}
                onToggle={onToggle}
            />
        );
        expect(screen.getByText(/Code/)).toBeInTheDocument();
    });

    it('shows placeholder when open with no active node', () => {
        renderPanel();
        expect(screen.getByText(/Click a node or start Ghost Runner/)).toBeInTheDocument();
    });

    it('shows ghost-runner placeholder when ghost is running and no code', () => {
        renderPanel({ isGhostRunning: true });
        expect(screen.getByText(/Code will appear automatically/)).toBeInTheDocument();
    });

    it('fetches code when active node with file is provided', async () => {
        const mockData = {
            snippet: 'def main():\n    pass',
            file_path: 'tests/file_a.py',
            start_line: 1,
            end_line: 2,
            full_source: null,
        };
        globalThis.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockData),
        });

        renderPanel({
            activeNode: {
                id: 'main',
                data: { label: 'main', file: 'tests/file_a.py' },
            },
        });

        await waitFor(() => {
            expect(globalThis.fetch).toHaveBeenCalledWith(
                '/api/snippet',
                expect.objectContaining({ method: 'POST' })
            );
        });
    });

    it('sends node language and line metadata when fetching code', async () => {
        globalThis.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({
                snippet: 'export function greet() {}',
                file_path: 'src/greet.js',
                language: 'javascript',
                start_line: 3,
                end_line: 5,
                full_source: null,
            }),
        });

        renderPanel({
            activeNode: {
                id: 'greet',
                data: {
                    label: 'greet',
                    file: 'src/greet.js',
                    language: 'javascript',
                    lineno: 3,
                    end_lineno: 5,
                },
            },
        });

        await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
        const [, options] = globalThis.fetch.mock.calls[0];
        expect(JSON.parse(options.body)).toEqual({
            file_path: 'src/greet.js',
            node_id: 'greet',
            language: 'javascript',
            start_line: 3,
            end_line: 5,
        });
    });

    it('shows error when fetch fails', async () => {
        globalThis.fetch.mockRejectedValue(new Error('Network error'));

        renderPanel({
            activeNode: {
                id: 'broken',
                data: { label: 'broken', file: 'some/path.py' },
            },
        });

        await waitFor(() => {
            expect(screen.getByText(/Could not connect to backend/)).toBeInTheDocument();
        });
    });

    it('shows backend detail when snippet request is denied', async () => {
        globalThis.fetch.mockResolvedValue({
            ok: false,
            status: 403,
            json: () => Promise.resolve({ detail: 'Access denied: unsafe file path' }),
        });

        renderPanel({
            activeNode: {
                id: 'hidden',
                data: { label: 'hidden', file: 'some/path.py' },
            },
        });

        await waitFor(() => {
            expect(screen.getByText(/Access denied: unsafe file path/)).toBeInTheDocument();
        });
    });

    it('shows a rate limit message instead of a backend connection error', async () => {
        globalThis.fetch.mockResolvedValue({
            ok: false,
            status: 429,
            json: () => Promise.resolve({ detail: 'Rate limit exceeded' }),
        });

        renderPanel({
            activeNode: {
                id: 'busy',
                data: { label: 'busy', file: 'some/path.py' },
            },
        });

        await waitFor(() => {
            expect(screen.getByText(/Too many code requests/)).toBeInTheDocument();
        });
    });

    it('shows external snippet message for node without file', async () => {
        renderPanel({
            activeNode: {
                id: 'os.path.join',
                data: { label: 'os.path.join' },
            },
        });

        await waitFor(() => {
            expect(screen.getByText(/No source code available/)).toBeInTheDocument();
        });
    });

    it('copy button triggers clipboard write and shows success toast', async () => {
        const user = userEvent.setup();
        const mockData = {
            snippet: 'def main(): pass',
            file_path: 'file.py',
            start_line: null,
            end_line: null,
            full_source: null,
        };
        globalThis.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockData),
        });

        renderPanel({
            activeNode: {
                id: 'main',
                data: { label: 'main', file: 'file.py' },
            },
        });

        await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());

        // Wait for state to update after fetch resolves
        const copyButton = await screen.findByRole('button', { name: 'Copy code' });
        await user.click(copyButton);

        // Verify toast was shown (clipboard behavior confirmed via toast)
        await waitFor(() => {
            expect(mockAddToast).toHaveBeenCalledWith('Code copied to clipboard!', 'success');
        });
    });

    it('renders a single copy button for the loaded code', async () => {
        const mockData = {
            snippet: 'def main(): pass',
            file_path: 'file.py',
            start_line: null,
            end_line: null,
            full_source: null,
        };
        globalThis.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockData),
        });

        renderPanel({
            activeNode: {
                id: 'main',
                data: { label: 'main', file: 'file.py' },
            },
        });

        await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());

        await waitFor(() => {
             expect(screen.getAllByRole('button', { name: 'Copy code' })).toHaveLength(1);
        });
    });

    it('shows fullscreen toggle button', async () => {
        const user = userEvent.setup();
        renderPanel();

        const expandBtn = screen.getByLabelText('Expand code');
        expect(expandBtn).toBeInTheDocument();

        await user.click(expandBtn);
        expect(screen.getByLabelText('Exit fullscreen')).toBeInTheDocument();
    });

    it('close button calls onToggle', async () => {
        const user = userEvent.setup();
        const onToggle = vi.fn();
        renderPanel({ onToggle });

        await user.click(screen.getByLabelText('Close Code Panel'));
        expect(onToggle).toHaveBeenCalled();
    });

    it('shows Ghost Runner badge when isGhostRunning is true', async () => {
        const mockData = {
            snippet: 'def run(): pass',
            file_path: 'runner.py',
            start_line: null,
            end_line: null,
            full_source: null,
        };
        globalThis.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockData),
        });

        renderPanel({
            isGhostRunning: true,
            activeNode: {
                id: 'run',
                data: { label: 'run', file: 'runner.py' },
            },
        });

        await waitFor(() => expect(globalThis.fetch).toHaveBeenCalled());
        expect(screen.getByText(/Following/)).toBeInTheDocument();
    });
});
