import React from 'react';

const speedOptions = [
    { label: 'Slow', value: 3500 },
    { label: 'Normal', value: 2500 },
    { label: 'Fast', value: 1200 },
];

const SimulationControls = ({ isPlaying, onToggle, onReset, stepCount = 0, speed = 1000, onSpeedChange, currentLabel = '' }) => {
    return (
        <div className="sim-controls">
            {/* Play/Pause */}
            <button
                onClick={onToggle}
                className={`sim-btn ${isPlaying ? 'sim-btn-pause' : 'sim-btn-play'}`}
                title={isPlaying ? 'Pause' : 'Play'}
            >
                {isPlaying ? '⏸' : '▶'}
            </button>

            {/* Reset */}
            <button
                onClick={onReset}
                className="sim-btn"
                title="Reset"
            >
                ↺
            </button>

            {/* Divider */}
            <div className="sim-divider" />

            {/* Speed Selector */}
            <div>
                {speedOptions.map(opt => (
                    <button
                        key={opt.value}
                        onClick={() => onSpeedChange && onSpeedChange(opt.value)}
                        className={`sim-speed ${speed === opt.value ? 'active' : ''}`}
                    >
                        {opt.label}
                    </button>
                ))}
            </div>

            {/* Divider */}
            <div className="sim-divider" />

            {/* Step Counter */}
            <div className="sim-step">
                Step <strong>{stepCount}</strong>
            </div>

            {/* Current Node Label */}
            {currentLabel && (
                <>
                    <div className="sim-divider" />
                    <div className="sim-current">
                        👻 {currentLabel}
                    </div>
                </>
            )}
        </div>
    );
};

export default SimulationControls;
