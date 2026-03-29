import React, { useState } from 'react';

const speedOptions = [
    { label: 'Slow', value: 3500 },
    { label: 'Normal', value: 2500 },
    { label: 'Fast', value: 1200 },
];

const strategyOptions = [
    { label: 'Smart', value: 'smart', icon: '🧠', hint: 'Entry points → DFS, hub pause' },
    { label: 'Entry Flow', value: 'entryFirst', icon: '🚀', hint: 'Follow execution flow' },
    { label: 'Hub Tour', value: 'hubsFirst', icon: '🔗', hint: 'Most connected first' },
    { label: 'By File', value: 'byFile', icon: '📁', hint: 'File by file traversal' },
    { label: 'Random', value: 'random', icon: '🎲', hint: 'Original random walk' },
];

const modeOptions = [
    { label: 'Auto', value: 'auto', icon: '▶' },
    { label: 'Explore', value: 'explore', icon: '🧭' },
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
}) => {
    const [showGuide, setShowGuide] = useState(false);
    const [showStrategyPicker, setShowStrategyPicker] = useState(false);

    const coveragePercent = totalNodes > 0 ? Math.round((visitedCount / totalNodes) * 100) : 0;
    const currentStrategy = strategyOptions.find(s => s.value === strategy) || strategyOptions[0];

    return (
        <div className="sim-controls">
            {/* Help */}
            <button
                onClick={() => setShowGuide(prev => !prev)}
                className={`sim-btn sim-btn-help ${showGuide ? 'active' : ''}`}
                title="What is this?"
                aria-label="Show guide"
                aria-expanded={showGuide}
            >
                <span aria-hidden="true">?</span>
            </button>

            {/* Guide Popover */}
            {showGuide && (
                <div className="sim-guide">
                    <button className="sim-guide-close" onClick={() => setShowGuide(false)} aria-label="Close guide"><span aria-hidden="true">✕</span></button>
                    <h4 className="sim-guide-title">Ghost Runner</h4>
                    <p>An intelligent code tracer that <strong>walks through your call graph</strong> using different strategies, highlighting functions and their connections in real time.</p>
                    <ul>
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
                    >
                        <span aria-hidden="true">{opt.icon}</span> {opt.label}
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
                <span aria-hidden="true">{isPlaying ? '⏸' : '▶'}</span>
            </button>

            {/* Reset */}
            <button
                onClick={onReset}
                className="sim-btn"
                title="Reset"
                aria-label="Reset simulation"
            >
                <span aria-hidden="true">↺</span>
            </button>

            <div className="sim-divider" />

            {/* Strategy Selector */}
            <div className="sim-strategy-wrapper">
                <button
                    onClick={() => setShowStrategyPicker(prev => !prev)}
                    className={`sim-strategy-btn ${showStrategyPicker ? 'active' : ''}`}
                    aria-label="Choose traversal strategy"
                    aria-expanded={showStrategyPicker}
                    title={currentStrategy.hint}
                >
                    <span aria-hidden="true">{currentStrategy.icon}</span> {currentStrategy.label}
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
                            >
                                <span className="sim-strategy-icon" aria-hidden="true">{opt.icon}</span>
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
                    >
                        {opt.label}
                    </button>
                ))}
            </div>

            <div className="sim-divider" />

            {/* Progress + Step Counter */}
            <div className="sim-progress" aria-live="polite">
                <div className="sim-progress-bar">
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
                        👻 {currentLabel}
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
