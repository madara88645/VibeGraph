import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import GhostTutorialPanel from './GhostTutorialPanel';
import { buildGhostTutorialView } from '../ghost/ghostTutorialMachine';

describe('GhostTutorialPanel', () => {
    it('renders acceptance criteria for the active phase', () => {
        const snapshot = {
            isPlaying: false,
            stepCount: 0,
            visitedCount: 0,
            totalNodes: 5,
            filesVisitedCount: 0,
            graphFileCount: 2,
        };
        const ghostTutorial = buildGhostTutorialView(snapshot);

        render(
            <GhostTutorialPanel
                ghostTutorial={ghostTutorial}
                stepSummaries={[]}
                totalNodes={5}
            />
        );

        expect(screen.getByText('Start the ghost')).toBeInTheDocument();
        expect(screen.getByText(/Press Play to start/)).toBeInTheDocument();
    });

    it('returns null when there is no graph', () => {
        const { container } = render(
            <GhostTutorialPanel
                ghostTutorial={buildGhostTutorialView({
                    isPlaying: false,
                    stepCount: 0,
                    visitedCount: 0,
                    totalNodes: 0,
                    filesVisitedCount: 0,
                    graphFileCount: 0,
                })}
                stepSummaries={[]}
                totalNodes={0}
            />
        );
        expect(container.firstChild).toBeNull();
    });
});
