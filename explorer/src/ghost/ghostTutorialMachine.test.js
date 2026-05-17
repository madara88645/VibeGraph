import { describe, expect, it } from 'vitest';

import {
    buildGhostTutorialView,
    getGhostTutorialPhaseIndex,
    GHOST_TUTORIAL_PHASES,
    phaseFullyMet,
} from './ghostTutorialMachine';

const base = {
    stepCount: 0,
    visitedCount: 0,
    totalNodes: 10,
    filesVisitedCount: 0,
    graphFileCount: 3,
};

describe('ghostTutorialMachine', () => {
    it('starts at phase 0 when idle', () => {
        const v = buildGhostTutorialView({ ...base, isPlaying: false });
        expect(v.phaseIndex).toBe(0);
        expect(v.runState).toBe('idle');
        expect(v.isComplete).toBe(false);
        expect(v.currentPhase?.id).toBe('press_play');
        expect(v.acceptance.every(a => !a.met)).toBe(true);
    });

    it('treats first completed step as satisfying the start gate even when paused', () => {
        const v = buildGhostTutorialView({ ...base, isPlaying: false, stepCount: 1 });
        expect(v.phaseIndex).toBe(1);
    });

    it('advances past press_play when playing', () => {
        expect(getGhostTutorialPhaseIndex({ ...base, isPlaying: true })).toBe(1);
        const v = buildGhostTutorialView({ ...base, isPlaying: true });
        expect(v.phaseIndex).toBe(1);
        expect(v.runState).toBe('active');
        expect(v.currentPhase?.id).toBe('take_steps');
    });

    it('requires four steps in phase take_steps', () => {
        expect(getGhostTutorialPhaseIndex({ ...base, isPlaying: true, stepCount: 3 })).toBe(1);
        expect(getGhostTutorialPhaseIndex({ ...base, isPlaying: true, stepCount: 4 })).toBe(2);
    });

    it('skips multi-file requirement when the graph has only one file', () => {
        const snap = {
            ...base,
            isPlaying: true,
            stepCount: 4,
            graphFileCount: 1,
            filesVisitedCount: 1,
        };
        expect(getGhostTutorialPhaseIndex(snap)).toBe(3);
    });

    it('requires two files when the graph has multiple files', () => {
        const snap = {
            ...base,
            isPlaying: true,
            stepCount: 4,
            graphFileCount: 2,
            filesVisitedCount: 1,
        };
        expect(getGhostTutorialPhaseIndex(snap)).toBe(2);
        expect(getGhostTutorialPhaseIndex({ ...snap, filesVisitedCount: 2 })).toBe(3);
    });

    it('completes pause_review only when paused with steps', () => {
        const snap = {
            ...base,
            isPlaying: true,
            stepCount: 4,
            graphFileCount: 1,
            filesVisitedCount: 1,
        };
        expect(getGhostTutorialPhaseIndex(snap)).toBe(3);
        expect(getGhostTutorialPhaseIndex({ ...snap, isPlaying: false })).toBe(4);
        const done = buildGhostTutorialView({ ...snap, isPlaying: false });
        expect(done.isComplete).toBe(true);
        expect(done.runState).toBe('complete');
        expect(done.currentPhase).toBe(null);
    });

    it('marks acceptance rows from the live snapshot', () => {
        const mid = buildGhostTutorialView({
            ...base,
            isPlaying: true,
            stepCount: 3,
            graphFileCount: 2,
            filesVisitedCount: 1,
        });
        expect(mid.currentPhase?.id).toBe('take_steps');
        expect(mid.acceptance.every(a => a.met)).toBe(false);

        const atFiles = buildGhostTutorialView({
            ...base,
            isPlaying: true,
            stepCount: 4,
            graphFileCount: 2,
            filesVisitedCount: 1,
        });
        expect(atFiles.currentPhase?.id).toBe('spread_files');
        expect(atFiles.acceptance[0].met).toBe(false);

        const atPauseLesson = buildGhostTutorialView({
            ...base,
            isPlaying: true,
            stepCount: 4,
            graphFileCount: 2,
            filesVisitedCount: 2,
        });
        expect(atPauseLesson.currentPhase?.id).toBe('pause_review');
        expect(atPauseLesson.acceptance[0].met).toBe(false);
    });

    it('phaseFullyMet matches aggregate of checks', () => {
        const p = GHOST_TUTORIAL_PHASES[1];
        expect(phaseFullyMet(p, { ...base, isPlaying: true, stepCount: 3 })).toBe(false);
        expect(phaseFullyMet(p, { ...base, isPlaying: true, stepCount: 4 })).toBe(true);
    });
});
