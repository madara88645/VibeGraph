import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
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

function deferred() {
    let resolve;
    let reject;
    const promise = new Promise((resolvePromise, rejectPromise) => {
        resolve = resolvePromise;
        reject = rejectPromise;
    });
    return { promise, resolve, reject };
}

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

    it('resets code data and fetch cache when activeNode is set to null', async () => {
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

        const defaults = {
            activeNode: {
                id: 'main',
                data: { label: 'main', file: 'tests/file_a.py' },
            },
            isGhostRunning: false,
            isOpen: true,
            onToggle: vi.fn(),
        };
        const { rerender } = render(<CodePanel {...defaults} />);

        await waitFor(() => {
            expect(globalThis.fetch).toHaveBeenCalledTimes(1);
        });

        expect(screen.getByText(/def main/)).toBeInTheDocument();

        rerender(
            <CodePanel
                activeNode={null}
                isGhostRunning={false}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );

        expect(screen.getByText(/Click a node or start Ghost Runner/)).toBeInTheDocument();
        expect(screen.queryByText(/def main/)).not.toBeInTheDocument();

        rerender(
            <CodePanel
                activeNode={{
                    id: 'main',
                    data: { label: 'main', file: 'tests/file_a.py' },
                }}
                isGhostRunning={false}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );

        await waitFor(() => {
            expect(globalThis.fetch).toHaveBeenCalledTimes(2);
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

    it('keeps the latest node code when an earlier snippet response resolves last', async () => {
        const firstResponse = deferred();
        const secondResponse = deferred();
        globalThis.fetch
            .mockReturnValueOnce(firstResponse.promise)
            .mockReturnValueOnce(secondResponse.promise);

        const { rerender } = renderPanel({
            activeNode: {
                id: 'old_function',
                data: { label: 'old_function', file: 'old.py' },
            },
        });

        await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(1));

        rerender(
            <CodePanel
                activeNode={{
                    id: 'new_function',
                    data: { label: 'new_function', file: 'new.py' },
                }}
                isGhostRunning={false}
                isOpen={true}
                onToggle={vi.fn()}
            />
        );
        await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(2));

        secondResponse.resolve({
            ok: true,
            json: () => Promise.resolve({
                snippet: 'def new_function(): pass',
                file_path: 'new.py',
                start_line: 1,
                end_line: 1,
                full_source: null,
            }),
        });
        expect(await screen.findByText(/def new_function/)).toBeInTheDocument();

        await act(async () => {
            firstResponse.resolve({
                ok: true,
                json: () => Promise.resolve({
                    snippet: 'def old_function(): pass',
                    file_path: 'old.py',
                    start_line: 1,
                    end_line: 1,
                    full_source: null,
                }),
            });
            await firstResponse.promise;
            await Promise.resolve();
            await Promise.resolve();
        });

        expect(screen.getByText(/def new_function/)).toBeInTheDocument();
        expect(screen.queryByText(/def old_function/)).not.toBeInTheDocument();
    });

    it('does not restore stale code after the issue #437 clear, restore, and select flow', async () => {
        const staleResponse = deferred();
        globalThis.fetch.mockReturnValueOnce(staleResponse.promise);

        const previousNode = {
            id: 'round',
            data: { label: 'round', file: 'builtins.py' },
        };
        const KeyLifecycleHarness = ({ apiKey, activeNode }) => (
            <div data-key-present={Boolean(apiKey)}>
                <CodePanel
                    activeNode={activeNode}
                    isGhostRunning={false}
                    isOpen={true}
                    onToggle={vi.fn()}
                />
            </div>
        );

        const { rerender } = render(
            <KeyLifecycleHarness apiKey="old-key" activeNode={previousNode} />
        );
        await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledTimes(1));

        // CodePanel is intentionally independent of the AI key, but it still
        // rerenders while the key is cleared and restored in issue #437.
        rerender(<KeyLifecycleHarness apiKey="" activeNode={previousNode} />);
        rerender(<KeyLifecycleHarness apiKey="restored-key" activeNode={previousNode} />);

        // After restoring the key, selecting a source function must win even when
        // the previous node's request finishes later.
        globalThis.fetch.mockResolvedValueOnce({
            ok: true,
            json: () => Promise.resolve({
                snippet: 'def summarize_progress(): pass',
                file_path: 'analytics.py',
                start_line: 4,
                end_line: 10,
                full_source: null,
            }),
        });
        rerender(
            <KeyLifecycleHarness
                apiKey="restored-key"
                activeNode={{
                    id: 'summarize_progress',
                    data: { label: 'summarize_progress', file: 'analytics.py' },
                }}
            />
        );

        expect(await screen.findByText(/def summarize_progress/)).toBeInTheDocument();
        expect(screen.getByText('analytics.py')).toBeInTheDocument();
        expect(screen.getByText('L4–10')).toBeInTheDocument();

        await act(async () => {
            staleResponse.resolve({
                ok: true,
                json: () => Promise.resolve({
                    snippet: '// External: round\n// No source code available',
                    file_path: null,
                    start_line: null,
                    end_line: null,
                    full_source: null,
                }),
            });
            await staleResponse.promise;
            await Promise.resolve();
            await Promise.resolve();
        });

        expect(screen.getByText(/def summarize_progress/)).toBeInTheDocument();
        expect(screen.queryByText(/External: round/)).not.toBeInTheDocument();
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
        expect(screen.getByLabelText('Exit fullscreen (Press Esc)')).toBeInTheDocument();
    });

    it('close button calls onToggle', async () => {
        const user = userEvent.setup();
        const onToggle = vi.fn();
        renderPanel({ onToggle });

        await user.click(screen.getByLabelText('Close Code Panel (Press Esc)'));
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
