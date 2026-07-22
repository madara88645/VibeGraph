import { afterEach, describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// SearchBar uses useReactFlow — mock before importing component.
// Hoisted spies so individual tests can assert how the viewport is moved.
const { getNodeMock, setCenterMock } = vi.hoisted(() => ({
    getNodeMock: vi.fn(),
    setCenterMock: vi.fn(),
}));

vi.mock('reactflow', () => ({
    useReactFlow: () => ({ getNode: getNodeMock, setCenter: setCenterMock }),
}));

import SearchBar from './SearchBar';

const MOCK_NODES = [
    { id: 'main', position: { x: 100, y: 100 }, data: { label: 'main', type: 'function', file: 'app.py' } },
    { id: 'FileProcessor', position: { x: 200, y: 200 }, data: { label: 'FileProcessor', type: 'class', file: 'models.py' } },
    { id: 'helper', position: { x: 300, y: 300 }, data: { label: 'helper', type: 'function', file: 'utils.py' } },
    { id: 'run', position: { x: 400, y: 400 }, data: { label: 'run', type: 'function', entry_point: true, file: 'app.py' } },
];

function renderSearchBar(overrides = {}) {
    const defaults = {
        allNodes: MOCK_NODES,
        onSelectNode: vi.fn(),
        onSelectFile: vi.fn(),
    };
    return render(<SearchBar {...defaults} {...overrides} />);
}

describe('SearchBar', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        getNodeMock.mockReturnValue(undefined);
    });

    it('renders search input with placeholder', () => {
        renderSearchBar();
        expect(screen.getByPlaceholderText(/Search nodes/)).toBeInTheDocument();
    });

    it('shows no results for empty query', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        const input = screen.getByPlaceholderText(/Search nodes/);
        await user.click(input);
        // No results shown for empty input
        expect(screen.queryByText('main')).not.toBeInTheDocument();
    });

    it('shows matching nodes when typing', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'main');
        expect(screen.getByText('main')).toBeInTheDocument();
    });

    it('filters by label (case-insensitive)', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'FILE');
        expect(screen.getByText('FileProcessor')).toBeInTheDocument();
        expect(screen.queryByText('helper')).not.toBeInTheDocument();
    });

    it('filters by file name', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'utils');
        expect(screen.getByText('helper')).toBeInTheDocument();
    });

    it('shows "No matching nodes found" for no matches', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'xyznonexistent');
        expect(screen.getByText(/No matching nodes found/)).toBeInTheDocument();
    });

    it('calls onSelectNode and onSelectFile when result is clicked', async () => {
        const user = userEvent.setup();
        const onSelectNode = vi.fn();
        const onSelectFile = vi.fn();
        renderSearchBar({ onSelectNode, onSelectFile });

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'main');
        await user.click(screen.getByText('main'));

        expect(onSelectNode).toHaveBeenCalledWith(
            expect.objectContaining({ id: 'main' })
        );
        expect(onSelectFile).toHaveBeenCalledWith('app.py');
    });

    it('clears query and closes results after selection', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'main');
        await user.click(screen.getByText('main'));

        // Input should be cleared
        expect(screen.getByPlaceholderText(/Search nodes/)).toHaveValue('');
    });

    it('clears query when ✕ button is clicked', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'main');
        expect(screen.getByTitle('Clear Search')).toBeInTheDocument();

        await user.click(screen.getByTitle('Clear Search'));
        expect(screen.getByPlaceholderText(/Search nodes/)).toHaveValue('');
    });

    it('navigates results with ArrowDown/ArrowUp', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        const input = screen.getByPlaceholderText(/Search nodes/);
        await user.type(input, 'a'); // matches main, FileProcessor, helper, run

        const items = screen.getAllByRole('option').filter((button) => (
            ['main', 'FileProcessor', 'helper', 'run'].some((label) => button.textContent?.includes(label))
        ));
        expect(items.length).toBeGreaterThan(0);

        await user.keyboard('{ArrowDown}');
        // highlightIdx is now 1 — no crash
    });

    it('selects highlighted result with Enter', async () => {
        const user = userEvent.setup();
        const onSelectNode = vi.fn();
        renderSearchBar({ onSelectNode });

        const input = screen.getByPlaceholderText(/Search nodes/);
        await user.type(input, 'main');
        await user.keyboard('{Enter}');

        expect(onSelectNode).toHaveBeenCalled();
    });

    it('closes results on Escape', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'main');
        expect(screen.getByText('main')).toBeInTheDocument();

        await user.keyboard('{Escape}');
        expect(screen.queryByText('main')).not.toBeInTheDocument();
    });

    it('selects existing query text on Ctrl+K so new typing replaces it (no append)', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        const input = screen.getByPlaceholderText(/Search nodes/);
        await user.type(input, 'summarize');
        expect(input).toHaveValue('summarize');

        // Re-open with Ctrl+K — existing text should become fully selected
        await user.keyboard('{Control>}k{/Control}');
        expect(input.selectionStart).toBe(0);
        expect(input.selectionEnd).toBe('summarize'.length);

        // Typing now replaces the selection instead of appending
        await user.keyboard('round');
        expect(input).toHaveValue('round');
    });

    it('opens search with Cmd+K (metaKey) on Mac', async () => {
        const user = userEvent.setup();
        renderSearchBar();

        const input = screen.getByPlaceholderText(/Search nodes/);
        await user.type(input, 'main');
        await user.keyboard('{Escape}');
        expect(screen.queryByText('main')).not.toBeInTheDocument();

        // Cmd+K should re-open and focus the input
        await user.keyboard('{Meta>}k{/Meta}');
        expect(input).toHaveFocus();
    });

    it('centers on the node\'s post-relayout position from the store (#460)', async () => {
        // Selecting a node in another file triggers a dagre re-layout that moves
        // the node. The store (getNode) returns its CURRENT laid-out position
        // once relayout settles; centering must use that, never the stale prop
        // position — that staleness is what drifted the camera to empty space.
        getNodeMock.mockImplementation((id) =>
            id === 'FileProcessor'
                ? { id, positionAbsolute: { x: 200, y: 100 }, width: 120, height: 40 }
                : undefined,
        );
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'FileProcessor');
        await user.click(screen.getByText('FileProcessor'));

        await waitFor(() => {
            expect(setCenterMock).toHaveBeenCalledTimes(1);
        });
        // node center = position + half of measured size
        expect(setCenterMock).toHaveBeenCalledWith(
            260,
            120,
            expect.objectContaining({ zoom: expect.any(Number) }),
        );
    });

    it('centers via the store on Enter selection too (#460)', async () => {
        getNodeMock.mockImplementation((id) =>
            id === 'helper'
                ? { id, positionAbsolute: { x: 300, y: 50 }, width: 100, height: 40 }
                : undefined,
        );
        const user = userEvent.setup();
        renderSearchBar();

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'helper');
        await user.keyboard('{Enter}');

        await waitFor(() => {
            expect(setCenterMock).toHaveBeenCalledTimes(1);
        });
        expect(setCenterMock).toHaveBeenCalledWith(
            350,
            70,
            expect.objectContaining({ zoom: expect.any(Number) }),
        );
    });

    it('limits results to 8 items', async () => {
        const user = userEvent.setup();
        const manyNodes = Array.from({ length: 20 }, (_, i) => ({
            id: `func_${i}`,
            position: { x: i * 10, y: 0 },
            data: { label: `func_${i}`, type: 'function', file: 'big.py' },
        }));
        renderSearchBar({ allNodes: manyNodes });

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'func');
        const results = screen.getAllByRole('option').filter((button) => (
            button.textContent?.includes('func_')
        ));
        expect(results.length).toBeLessThanOrEqual(8);
    });

    describe('explanation panel occlusion (#560)', () => {
        const setPanelVars = () => {
            document.documentElement.style.setProperty('--explanation-panel-width', '330px');
            document.documentElement.style.setProperty('--explanation-panel-edge-offset', '16px');
        };
        const clearPanelVars = () => {
            document.documentElement.style.removeProperty('--explanation-panel-width');
            document.documentElement.style.removeProperty('--explanation-panel-edge-offset');
        };
        const setViewportWidth = (width) => {
            Object.defineProperty(window, 'innerWidth', {
                configurable: true,
                writable: true,
                value: width,
            });
        };
        const originalWidth = window.innerWidth;

        beforeEach(() => {
            setPanelVars();
            getNodeMock.mockImplementation((id) =>
                id === 'FileProcessor'
                    ? { id, positionAbsolute: { x: 200, y: 100 }, width: 120, height: 40 }
                    : undefined,
            );
        });

        afterEach(() => {
            clearPanelVars();
            setViewportWidth(originalWidth);
        });

        it('offsets the target so the node does not land behind the panel', async () => {
            setViewportWidth(1280);
            const user = userEvent.setup();
            renderSearchBar();

            await user.type(screen.getByPlaceholderText(/Search nodes/), 'FileProcessor');
            await user.click(screen.getByText('FileProcessor'));

            await waitFor(() => {
                expect(setCenterMock).toHaveBeenCalledTimes(1);
            });
            // Node center is x=260. The panel covers 330 + 16 = 346px on the
            // right, so the camera targets half of that further right, in flow
            // units: 260 + (346 / 2) / 1.5 = 375.33…
            const [x, y] = setCenterMock.mock.calls[0];
            expect(x).toBeCloseTo(375.33, 1);
            expect(y).toBe(120);
        });

        it('does not offset below the mobile breakpoint, where the panel is a bottom sheet', async () => {
            setViewportWidth(375);
            const user = userEvent.setup();
            renderSearchBar();

            await user.type(screen.getByPlaceholderText(/Search nodes/), 'FileProcessor');
            await user.click(screen.getByText('FileProcessor'));

            await waitFor(() => {
                expect(setCenterMock).toHaveBeenCalledTimes(1);
            });
            expect(setCenterMock.mock.calls[0][0]).toBe(260);
        });
    });
});
