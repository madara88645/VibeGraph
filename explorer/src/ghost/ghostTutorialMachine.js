/**
 * Ghost Runner guided tutorial — explicit phase graph + acceptance checks.
 * Pure functions only (easy to unit test).
 */

export const GHOST_TUTORIAL_PHASES = [
    {
        id: 'press_play',
        title: 'Start the ghost',
        summary: 'Kick off an animated walk so you can watch calls flow across your graph.',
        checks: [
            {
                id: 'started',
                label: 'Press Play to start Ghost Runner (stays checked after your first step)',
                test: s => s.isPlaying || s.stepCount >= 1,
            },
        ],
    },
    {
        id: 'take_steps',
        title: 'Follow a short path',
        summary: 'Let the ghost move at least four times so the trail and highlights make sense.',
        checks: [{ id: 'steps', label: 'Complete at least 4 ghost steps', test: s => s.stepCount >= 4 }],
    },
    {
        id: 'spread_files',
        title: 'Touch more of the codebase',
        summary:
            'When several files exist, visit nodes from at least two files. Single-file graphs skip this automatically.',
        checks: [
            {
                id: 'files',
                label: 'Visit nodes from 2+ different files (skipped if the graph is one file)',
                test: s => s.graphFileCount <= 1 || s.filesVisitedCount >= 2,
            },
        ],
    },
    {
        id: 'pause_review',
        title: 'Pause and read the recap',
        summary: 'Stop playback once so you can skim coverage, files touched, and your recent steps.',
        checks: [
            {
                id: 'paused',
                label: 'Pause Ghost Runner after you have taken steps',
                test: s => !s.isPlaying && s.stepCount > 0,
            },
        ],
    },
];

/** @typedef {'idle' | 'active' | 'complete'} GhostTutorialRunState */

/**
 * @param {typeof GHOST_TUTORIAL_PHASES[number]} phase
 * @param {GhostTutorialSnapshot} snapshot
 */
export function phaseFullyMet(phase, snapshot) {
    return phase.checks.every(c => c.test(snapshot));
}

/**
 * Index of the first phase not yet fully satisfied. Equal to length when all done.
 * @param {GhostTutorialSnapshot} snapshot
 */
export function getGhostTutorialPhaseIndex(snapshot) {
    let i = 0;
    while (i < GHOST_TUTORIAL_PHASES.length && phaseFullyMet(GHOST_TUTORIAL_PHASES[i], snapshot)) {
        i += 1;
    }
    return i;
}

/**
 * @typedef {{
 *   isPlaying: boolean,
 *   stepCount: number,
 *   visitedCount: number,
 *   totalNodes: number,
 *   filesVisitedCount: number,
 *   graphFileCount: number,
 * }} GhostTutorialSnapshot
 */

/**
 * @param {GhostTutorialSnapshot} snapshot
 * @returns {{
 *   runState: GhostTutorialRunState,
 *   phaseIndex: number,
 *   phasesTotal: number,
 *   isComplete: boolean,
 *   currentPhase: typeof GHOST_TUTORIAL_PHASES[number] | null,
 *   acceptance: Array<{ id: string, label: string, met: boolean }>,
 *   progressLabel: string,
 * }}
 */
export function buildGhostTutorialView(snapshot) {
    const phaseIndex = getGhostTutorialPhaseIndex(snapshot);
    const isComplete = phaseIndex >= GHOST_TUTORIAL_PHASES.length;
    const currentPhase = !isComplete ? GHOST_TUTORIAL_PHASES[phaseIndex] : null;

    let runState = 'active';
    if (isComplete) {
        runState = 'complete';
    } else if (phaseIndex === 0 && !snapshot.isPlaying) {
        runState = 'idle';
    }

    const acceptance = currentPhase
        ? currentPhase.checks.map(c => ({
              id: c.id,
              label: c.label,
              met: c.test(snapshot),
          }))
        : [];

    const progressLabel = isComplete
        ? 'Guided tour complete'
        : `Guided tour · step ${phaseIndex + 1} of ${GHOST_TUTORIAL_PHASES.length}`;

    return {
        runState,
        phaseIndex,
        phasesTotal: GHOST_TUTORIAL_PHASES.length,
        isComplete,
        currentPhase,
        acceptance,
        progressLabel,
    };
}
