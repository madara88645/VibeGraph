import React, { useState, useEffect, useRef } from 'react';

import {
    IconClose,
    IconCompass,
    IconGhost,
    IconHelp,
    IconModule,
    IconNetwork,
    IconPause,
    IconPlay,
    IconEntry,
    IconReset,
    IconShuffle,
    IconSparkles,
} from './icons';

const speedOptions = [
    { label: 'Slow', value: 3500 },
    { label: 'Normal', value: 2500 },
    { label: 'Fast', value: 1200 },
];

const strategyOptions = [
    { label: 'Smart', value: 'smart', Icon: IconSparkles, hint: 'Entry points → DFS, hub pause' },
    { label: 'Entry Flow', value: 'entryFirst', Icon: IconEntry, hint: 'Follow execution flow' },
    { label: 'Hub Tour', value: 'hubsFirst', Icon: IconNetwork, hint: 'Most connected first' },
    { label: 'By File', value: 'byFile', Icon: IconModule, hint: 'File by file traversal' },
    { label: 'Random', value: 'random', Icon: IconShuffle, hint: 'Original random walk' },
];

const modeOptions = [
    { label: 'Auto', value: 'auto', Icon: IconPlay },
    { label: 'Explore', value: 'explore', Icon: IconCompass },
];

const SimulationControls = ({
    isPlaying,
    onToggle,
    onReset,
    stepCount = 0,
    speed = 2500,
    onSpeedChange,
    currentLabel = '',
    strategy = 'smart',
    onStrategyChange,
    mode = 'auto',
    onModeChange,
    visitedCount = 0,
    totalNodes = 0,
    showTutorial = true,
    onToggleTutorial,
}) => {
    const [showGuide, setShowGuide] = useState(false);
    const [showStrategyPicker, setShowStrategyPicker] = useState(false);

    const helpButtonRef = useRef(null);
    const guideRef = useRef(null);
    const strategyWrapperRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (showGuide) {
                const clickOnHelpButton = helpButtonRef.current && helpButtonRef.current.contains(event.target);
                const clickInsideGuide = guideRef.current && guideRef.current.contains(event.target);
                if (!clickOnHelpButton && !clickInsideGuide) {
                    setShowGuide(false);
                }
            }

            if (showStrategyPicker) {
                if (strategyWrapperRef.current && !strategyWrapperRef.current.contains(event.target)) {
                    setShowStrategyPicker(false);
                }
            }
        };

        const handleKeyDown = (event) => {
            if (event.key === 'Escape') {
                if (showGuide) {
                    setShowGuide(false);
                }
                if (showStrategyPicker) {
                    setShowStrategyPicker(false);
                }
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        document.addEventListener('keydown', handleKeyDown);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, [showGuide, showStrategyPicker]);

    const coveragePercent = totalNodes > 0 ? Math.round((visitedCount / totalNodes) * 100) : 0;
    const currentStrategy = strategyOptions.find(s => s.value === strategy) || strategyOptions[0];

    return (
        <div className="sim-controls">
            {/* Help */}
            <button
                ref={helpButtonRef}
                onClick={() => setShowGuide(prev => !prev)}
                className={`sim-btn sim-btn-help ${showGuide ? 'active' : ''}`}
                title="What is this?"
                aria-label="Show guide"
                aria-expanded={showGuide}
            >
                <IconHelp size={15} />
            </button>

            {/* Guided Tour Toggle */}
            {totalNodes > 0 && (
                <button
                    onClick={() => onToggleTutorial && onToggleTutorial()}
                    className={`sim-btn sim-btn-tour ${showTutorial ? 'active' : ''}`}
                    title="Toggle Guided Tour Checklist"
                    aria-label="Toggle Guided Tour Checklist"
                    aria-expanded={showTutorial}
                >
                    <IconGhost size={15} />
                </button>
            )}


            {/* Guide Popover */}
            {showGuide && (
                <div className="sim-guide" ref={guideRef}>
                    <button className="sim-guide-close" onClick={() => setShowGuide(false)} aria-label="Close guide" title="Close guide"><IconClose size={13} /></button>
                    <h4 className="sim-guide-title">Ghost Runner</h4>
                    <p>An intelligent code tracer that <strong>walks through your call graph</strong> using different strategies, highlighting functions and their connections in real time.</p>
                    <ul>
                        <li><strong>Guided tour</strong> — Follow the checklist above the narration to learn Ghost Runner in four short beats</li>
                        <li><strong>Strategies</strong> — Smart (DFS from entry points), Entry Flow, Hub Tour, By File, or Random</li>
                        <li><strong>Modes</strong> — Auto (ghost walks alone) or Explore (you guide the ghost)</li>
                        <li><strong>Speed</strong> — Control how fast the ghost moves between nodes</li>
                        <li><strong>Trail</strong> — The last 4 visited nodes stay highlighted so you can follow the path</li>
                        <li><strong>Progress</strong> — Track how much of the codebase you've explored</li>
                    </ul>
                    <h4 className="sim-guide-title">Code Analyzer</h4>
                    <p>Upload any Python project and the analyzer will <strong>parse the AST</strong> (Abstract Syntax Tree) to build an interactive call graph showing:</p>
                    <ul>
                        <li><strong>Functions, classes & entry points</strong> as nodes</li>
                        <li><strong>Function calls</strong> as edges between nodes</li>
                        <li><strong>File dependencies</strong> — which files import what</li>
                    </ul>
                    <p className="sim-guide-hint">Click any node for an AI-powered explanation, or use the chat to ask questions about the code.</p>
                </div>
            )}

            <div className="sim-divider" />

            {/* Mode Toggle */}
            <div role="group" aria-label="Ghost mode" className="sim-mode-group">
                {modeOptions.map(opt => (
                    <button
                        key={opt.value}
                        onClick={() => onModeChange && onModeChange(opt.value)}
                        className={`sim-mode-btn ${mode === opt.value ? 'active' : ''}`}
                        aria-pressed={mode === opt.value}
                        title={opt.value === 'auto' ? 'Ghost walks automatically' : 'You guide the ghost'}
                        aria-label={opt.value === 'auto' ? 'Auto mode: Ghost walks automatically' : 'Explore mode: You guide the ghost'}
                    >
                        <opt.Icon size={13} /> {opt.label}
                    </button>
                ))}
            </div>

            <div className="sim-divider" />

            {/* Play/Pause */}
            <button
                onClick={onToggle}
                className={`sim-btn ${isPlaying ? 'sim-btn-pause' : 'sim-btn-play'}`}
                title={isPlaying ? 'Pause' : 'Play'}
                aria-label={isPlaying ? 'Pause simulation' : 'Play simulation'}
                aria-pressed={isPlaying}
            >
                {isPlaying ? <IconPause size={14} /> : <IconPlay size={14} />}
            </button>

            {/* Reset */}
            <button
                onClick={onReset}
                className="sim-btn"
                title="Reset"
                aria-label="Reset simulation"
            >
                <IconReset size={15} />
            </button>

            <div className="sim-divider" />

            {/* Strategy Selector */}
            <div className="sim-strategy-wrapper" ref={strategyWrapperRef}>
                <button
                    onClick={() => setShowStrategyPicker(prev => !prev)}
                    className={`sim-strategy-btn ${showStrategyPicker ? 'active' : ''}`}
                    aria-label={`Traversal strategy: ${currentStrategy.label}. ${currentStrategy.hint}`}
                    aria-expanded={showStrategyPicker}
                    title={currentStrategy.hint}
                >
                    <currentStrategy.Icon size={14} /> {currentStrategy.label}
                </button>

                {showStrategyPicker && (
                    <div className="sim-strategy-picker">
                        {strategyOptions.map(opt => (
                            <button
                                key={opt.value}
                                onClick={() => {
                                    onStrategyChange && onStrategyChange(opt.value);
                                    setShowStrategyPicker(false);
                                }}
                                className={`sim-strategy-option ${strategy === opt.value ? 'active' : ''}`}
                                aria-pressed={strategy === opt.value}
                                aria-label={`${opt.label} strategy: ${opt.hint}`}
                            >
                                <opt.Icon className="sim-strategy-icon" size={16} />
                                <span className="sim-strategy-label">{opt.label}</span>
                                <span className="sim-strategy-hint">{opt.hint}</span>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="sim-divider" />

            {/* Speed Selector */}
            <div role="group" aria-label="Simulation speed">
                {speedOptions.map(opt => (
                    <button
                        key={opt.value}
                        onClick={() => onSpeedChange && onSpeedChange(opt.value)}
                        className={`sim-speed ${speed === opt.value ? 'active' : ''}`}
                        aria-pressed={speed === opt.value}
                        aria-label={`Set simulation speed to ${opt.label}`}
                    >
                        {opt.label}
                    </button>
                ))}
            </div>

            <div className="sim-divider" />

            {/* Progress + Step Counter */}
            <div className="sim-progress" aria-live="polite">
                <div
                    className="sim-progress-bar"
                    role="progressbar"
                    aria-valuenow={coveragePercent}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label="Simulation coverage progress"
                >
                    <div
                        className="sim-progress-fill"
                        style={{ width: `${coveragePercent}%` }}
                    />
                </div>
                <span className="sim-progress-text">
                    {visitedCount}/{totalNodes} <span className="sim-progress-pct">({coveragePercent}%)</span>
                </span>
            </div>

            <div className="sim-divider" />

            {/* Step Counter */}
            <div className="sim-step" aria-live="polite">
                Step <strong>{stepCount}</strong>
            </div>

            {/* Current Node Label */}
            {currentLabel && (
                <>
                    <div className="sim-divider" />
                    <div className="sim-current" aria-live="polite">
                        <IconGhost size={13} /> {currentLabel}
                    </div>
                </>
            )}

            {/* Explore mode hint */}
            {mode === 'explore' && isPlaying && !currentLabel && (
                <>
                    <div className="sim-divider" />
                    <div className="sim-explore-hint" aria-live="polite">
                        Press Play to start exploring...
                    </div>
                </>
            )}
        </div>
    );
};

export default SimulationControls;
