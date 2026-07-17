import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import GhostChoices from './GhostChoices';

const NODES = [
    { id: 'alpha', data: { label: 'Alpha', file: 'a.py', entry_point: true } },
    { id: 'beta', data: { label: 'Beta', file: 'b.py', type: 'class' } },
];

function renderChoices(props = {}) {
    const defaults = {
        availableNextNodes: NODES,
        onChoose: vi.fn(),
        isPlaying: true,
        mode: 'explore',
    };
    return render(<GhostChoices {...defaults} {...props} />);
}

describe('GhostChoices', () => {
    it('renders the choices when mode is explore, playing, and nodes are available', () => {
        renderChoices();
        expect(screen.getByText('Where should the ghost go next?')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Go to Alpha/ })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Go to Beta/ })).toBeInTheDocument();
    });

    it('renders null when mode is not explore', () => {
        const { container } = renderChoices({ mode: 'guided' });
        expect(container.firstChild).toBeNull();
    });

    it('renders null when not playing', () => {
        const { container } = renderChoices({ isPlaying: false });
        expect(container.firstChild).toBeNull();
    });

    it('renders null when there are no available nodes', () => {
        const { container } = renderChoices({ availableNextNodes: [] });
        expect(container.firstChild).toBeNull();
    });

    it('calls onChoose with the first node id when the "1" key is pressed', () => {
        const onChoose = vi.fn();
        renderChoices({ onChoose });

        fireEvent.keyDown(window, { key: '1' });

        expect(onChoose).toHaveBeenCalledTimes(1);
        expect(onChoose).toHaveBeenCalledWith('alpha');
    });

    it('ignores an out-of-range number key', () => {
        const onChoose = vi.fn();
        renderChoices({ onChoose });

        fireEvent.keyDown(window, { key: '5' });

        expect(onChoose).not.toHaveBeenCalled();
    });

    it('ignores number keys pressed with a modifier held', () => {
        const onChoose = vi.fn();
        renderChoices({ onChoose });

        fireEvent.keyDown(window, { key: '1', ctrlKey: true });
        fireEvent.keyDown(window, { key: '1', metaKey: true });
        fireEvent.keyDown(window, { key: '1', altKey: true });

        expect(onChoose).not.toHaveBeenCalled();
    });

    it('ignores number keys while focus is inside an input or textarea', () => {
        const onChoose = vi.fn();
        render(
            <>
                <input aria-label="text-field" />
                <textarea aria-label="text-area" />
                <GhostChoices
                    availableNextNodes={NODES}
                    onChoose={onChoose}
                    isPlaying
                    mode="explore"
                />
            </>
        );

        screen.getByLabelText('text-field').focus();
        fireEvent.keyDown(window, { key: '1' });

        screen.getByLabelText('text-area').focus();
        fireEvent.keyDown(window, { key: '1' });

        expect(onChoose).not.toHaveBeenCalled();
    });

    it('calls onChoose with the node id when a choice button is clicked', async () => {
        const user = userEvent.setup();
        const onChoose = vi.fn();
        renderChoices({ onChoose });

        await user.click(screen.getByRole('button', { name: /Go to Beta/ }));

        expect(onChoose).toHaveBeenCalledTimes(1);
        expect(onChoose).toHaveBeenCalledWith('beta');
    });
});
