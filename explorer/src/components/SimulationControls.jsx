import React from 'react'

export default function SimulationControls({
  isPlaying,
  speed,
  onPlay,
  onPause,
  onReset,
  onSpeedChange,
  currentStep,
  totalSteps,
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        padding: '6px 14px',
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
      }}
    >
      <span
        style={{
          fontWeight: 700,
          fontSize: '11px',
          color: 'var(--accent-entry)',
          letterSpacing: '0.05em',
        }}
      >
        👻 GHOST RUNNER
      </span>

      <button
        className="btn-primary"
        onClick={isPlaying ? onPause : onPlay}
        title={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? '⏸ Pause' : '▶ Play'}
      </button>

      <button className="btn-ghost" onClick={onReset} title="Reset">
        ⏹ Reset
      </button>

      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)', fontSize: '12px' }}>
        Speed
        <input
          type="range"
          min={0.5}
          max={3}
          step={0.25}
          value={speed}
          onChange={(e) => onSpeedChange(Number(e.target.value))}
          style={{ accentColor: 'var(--accent-fn)', width: '80px' }}
        />
        <span style={{ minWidth: '28px' }}>{speed}×</span>
      </label>

      {totalSteps > 0 && (
        <span style={{ color: 'var(--text-muted)', fontSize: '11px', marginLeft: 'auto' }}>
          Step {currentStep + 1} / {totalSteps}
        </span>
      )}
    </div>
  )
}
