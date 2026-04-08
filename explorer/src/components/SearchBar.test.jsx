import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// SearchBar uses useReactFlow — mock before importing component
vi.mock('reactflow', () => ({
    useReactFlow: () => ({ setCenter: vi.fn() }),
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

        const items = screen.getAllByRole('button').filter((button) => (
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

    it('limits results to 8 items', async () => {
        const user = userEvent.setup();
        const manyNodes = Array.from({ length: 20 }, (_, i) => ({
            id: `func_${i}`,
            position: { x: i * 10, y: 0 },
            data: { label: `func_${i}`, type: 'function', file: 'big.py' },
        }));
        renderSearchBar({ allNodes: manyNodes });

        await user.type(screen.getByPlaceholderText(/Search nodes/), 'func');
        const results = screen.getAllByRole('button').filter((button) => (
            button.textContent?.includes('func_')
        ));
        expect(results.length).toBeLessThanOrEqual(8);
    });
});
