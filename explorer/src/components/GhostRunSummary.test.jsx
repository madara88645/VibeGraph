import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';

import GhostRunSummary from './GhostRunSummary';

const RUN_SUMMARY = {
    visitedCount: 3,
    totalNodes: 10,
    filesVisited: 2,
    mostConnected: { label: 'hub', degree: 5 },
    unvisitedEntries: ['main'],
    guidedTourComplete: false,
    recentSteps: [{ step: 1, label: 'start' }],
};

// The component uses setTimeout for enter (0ms) and exit (0ms then 250ms) transitions.
function flushTimers(ms = 300) {
    act(() => {
        vi.advanceTimersByTime(ms);
    });
}

describe('GhostRunSummary', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('renders the summary when paused with visited nodes', () => {
        render(<GhostRunSummary runSummary={RUN_SUMMARY} isPlaying={false} />);
        flushTimers();

        expect(screen.getByText('Run summary')).toBeInTheDocument();
        expect(screen.getByText('Where you just were')).toBeInTheDocument();
    });

    it('renders null while the ghost is still playing', () => {
        const { container } = render(
            <GhostRunSummary runSummary={RUN_SUMMARY} isPlaying />
        );
        flushTimers();

        expect(container.firstChild).toBeNull();
        expect(screen.queryByText('Run summary')).not.toBeInTheDocument();
    });

    it('renders null when no nodes were visited', () => {
        const { container } = render(
            <GhostRunSummary
                runSummary={{ visitedCount: 0, totalNodes: 5 }}
                isPlaying={false}
            />
        );
        flushTimers();

        expect(container.firstChild).toBeNull();
    });

    it('does not crash when runSummary lacks unvisitedEntries (regression #493)', () => {
        // Issue #493: `unvisitedEntries` must default to [] so a summary object that
        // omits the field does not throw on `unvisitedEntries.length`.
        const runSummaryWithoutEntries = {
            visitedCount: 2,
            totalNodes: 4,
            filesVisited: 1,
            // unvisitedEntries intentionally omitted (undefined)
        };

        expect(() => {
            render(
                <GhostRunSummary
                    runSummary={runSummaryWithoutEntries}
                    isPlaying={false}
                />
            );
            flushTimers();
        }).not.toThrow();

        expect(screen.getByText('Run summary')).toBeInTheDocument();
    });
});
