import React from 'react';

const speedOptions = [
    { label: 'Slow', value: 3500 },
    { label: 'Normal', value: 2500 },
    { label: 'Fast', value: 1200 },
];

const SimulationControls = ({ isPlaying, onToggle, onReset, stepCount = 0, speed = 1000, onSpeedChange, currentLabel = '' }) => {
    return (
        <div style={{
            position: 'absolute',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(15, 15, 28, 0.92)',
            padding: '8px 16px',
            borderRadius: '40px',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            zIndex: 100,
            fontFamily: "'Inter', system-ui, sans-serif",
        }}>
            {/* Play/Pause */}
            <button
                onClick={onToggle}
                style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    border: 'none',
                    background: isPlaying
                        ? 'rgba(244, 63, 94, 0.15)'
                        : 'rgba(34, 197, 94, 0.15)',
                    color: isPlaying ? '#f43f5e' : '#22c55e',
                    fontSize: '1rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s',
                }}
                title={isPlaying ? 'Pause' : 'Play'}
            >
                {isPlaying ? '⏸' : '▶'}
            </button>

            {/* Reset */}
            <button
                onClick={onReset}
                style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '50%',
                    border: '1px solid rgba(255,255,255,0.08)',
                    background: 'transparent',
                    color: '#94a3b8',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s',
                }}
                title="Reset"
            >
                ↺
            </button>

            {/* Divider */}
            <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)' }} />

            {/* Speed Selector */}
            <div style={{ display: 'flex', gap: '2px' }}>
                {speedOptions.map(opt => (
                    <button
                        key={opt.value}
                        onClick={() => onSpeedChange && onSpeedChange(opt.value)}
                        style={{
                            padding: '3px 8px',
                            borderRadius: '12px',
                            border: 'none',
                            background: speed === opt.value ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                            color: speed === opt.value ? '#3b82f6' : '#64748b',
                            fontSize: '0.7rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            transition: 'all 0.15s',
                        }}
                    >
                        {opt.label}
                    </button>
                ))}
            </div>

            {/* Divider */}
            <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)' }} />

            {/* Step Counter */}
            <div style={{
                fontSize: '0.72rem',
                color: '#64748b',
                fontWeight: 500,
                minWidth: '50px',
                textAlign: 'center',
            }}>
                Step <span style={{ color: '#e2e8f0', fontWeight: 700 }}>{stepCount}</span>
            </div>

            {/* Current Node Label */}
            {currentLabel && (
                <>
                    <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.08)' }} />
                    <div style={{
                        fontSize: '0.7rem',
                        color: '#f43f5e',
                        fontWeight: 600,
                        maxWidth: '120px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                    }}>
                        👻 {currentLabel}
                    </div>
                </>
            )}
        </div>
    );
};

export default SimulationControls;
