import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';

import GhostNarration from './GhostNarration';

// The typewriter advances one character every 18ms.
const TICK = 18;

describe('GhostNarration', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('types out the narration text as the timers advance', () => {
        render(<GhostNarration narration={{ narration: 'Hello world' }} isPlaying />);

        // Nothing shows until the typewriter has produced at least one character.
        expect(screen.queryByText('Hello world')).not.toBeInTheDocument();

        act(() => {
            vi.advanceTimersByTime(TICK * 5);
        });
        expect(screen.getByText('Hello')).toBeInTheDocument();
        expect(screen.queryByText('Hello world')).not.toBeInTheDocument();

        act(() => {
            vi.advanceTimersByTime(TICK * 6);
        });
        expect(screen.getByText('Hello world')).toBeInTheDocument();
    });

    it('does not restart typing when the same narration object is passed again', () => {
        const narration = { narration: 'Hello world' };
        const { rerender } = render(<GhostNarration narration={narration} isPlaying />);

        act(() => {
            vi.advanceTimersByTime(TICK * 11);
        });
        expect(screen.getByText('Hello world')).toBeInTheDocument();

        // Re-rendering with the SAME object reference must not reset the text to empty.
        rerender(<GhostNarration narration={narration} isPlaying />);

        expect(screen.getByText('Hello world')).toBeInTheDocument();
    });

    it('hides the narration after the ghost stops playing', () => {
        const narration = { narration: 'Hello world' };
        const { rerender } = render(<GhostNarration narration={narration} isPlaying />);

        act(() => {
            vi.advanceTimersByTime(TICK * 11);
        });
        expect(screen.getByText('Hello world')).toBeInTheDocument();

        rerender(<GhostNarration narration={narration} isPlaying={false} />);
        act(() => {
            vi.advanceTimersByTime(1500);
        });

        expect(screen.queryByText('Hello world')).not.toBeInTheDocument();
    });
});
