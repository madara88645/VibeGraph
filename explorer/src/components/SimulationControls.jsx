import React, { useState } from 'react';

const speedOptions = [
    { label: 'Slow', value: 3500 },
    { label: 'Normal', value: 2500 },
    { label: 'Fast', value: 1200 },
];

const SimulationControls = ({ isPlaying, onToggle, onReset, stepCount = 0, speed = 1000, onSpeedChange, currentLabel = '' }) => {
    const [showGuide, setShowGuide] = useState(false);

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
                ?
            </button>

            {/* Guide Popover */}
            {showGuide && (
                <div className="sim-guide">
                    <button className="sim-guide-close" onClick={() => setShowGuide(false)} aria-label="Close guide">✕</button>
                    <h4 className="sim-guide-title">Ghost Runner</h4>
                    <p>A visual code tracer that <strong>randomly walks through your call graph</strong>, highlighting functions and their connections in real time.</p>
                    <ul>
                        <li><strong>Play/Pause</strong> — Start or stop the traversal</li>
                        <li><strong>Speed</strong> — Control how fast the ghost moves between nodes</li>
                        <li><strong>Trail</strong> — The last 4 visited nodes stay highlighted so you can follow the path</li>
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

            {/* Play/Pause */}
            <button
                onClick={onToggle}
                className={`sim-btn ${isPlaying ? 'sim-btn-pause' : 'sim-btn-play'}`}
                title={isPlaying ? 'Pause' : 'Play'}
                aria-label={isPlaying ? 'Pause simulation' : 'Play simulation'}
                aria-pressed={isPlaying}
            >
                {isPlaying ? '⏸' : '▶'}
            </button>

            {/* Reset */}
            <button
                onClick={onReset}
                className="sim-btn"
                title="Reset"
                aria-label="Reset simulation"
            >
                ↺
            </button>

            {/* Divider */}
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

            {/* Divider */}
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
        </div>
    );
};

export default SimulationControls;
