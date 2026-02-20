import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const LEVELS = ['beginner', 'intermediate', 'advanced']
const TABS = ['technical', 'analogy']

export default function ExplanationPanel({ activeNode, onClose }) {
  const [level, setLevel] = useState('beginner')
  const [tab, setTab] = useState('technical')
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function fetchExplanation(selectedLevel) {
    if (!activeNode) return
    setLoading(true)
    setError(null)
    setExplanation(null)
    try {
      const res = await fetch('/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: activeNode.id,
          node_label: activeNode.data.label,
          source_code: activeNode.data.source ?? '',
          level: selectedLevel,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? `HTTP ${res.status}`)
      }
      const data = await res.json()
      setExplanation(data.explanation)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function handleLevelChange(l) {
    setLevel(l)
    fetchExplanation(l)
  }

  if (!activeNode) return null

  return (
    <div
      style={{
        width: 'var(--explanation-width)',
        background: 'var(--bg-secondary)',
        borderLeft: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '8px 12px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span style={{ fontWeight: 700, color: 'var(--accent-fn)', fontSize: '13px' }}>
          🤖 AI Explanation
        </span>
        <button className="btn-ghost" onClick={onClose} style={{ padding: '2px 8px' }}>✕</button>
      </div>

      {/* Node label */}
      <div style={{ padding: '6px 12px', borderBottom: '1px solid var(--border)', fontSize: '12px', color: 'var(--text-secondary)' }}>
        Explaining: <strong style={{ color: 'var(--text-primary)' }}>{activeNode.data.label}</strong>
      </div>

      {/* Level buttons */}
      <div style={{ display: 'flex', gap: '4px', padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
        {LEVELS.map((l) => (
          <button
            key={l}
            className={`btn-ghost${level === l ? ' active' : ''}`}
            onClick={() => handleLevelChange(l)}
            style={{ flex: 1, fontSize: '11px' }}
          >
            {l}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab${tab === t ? ' active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t === 'technical' ? '🔧 Technical' : '🎭 Analogy'}
          </button>
        ))}
      </div>

      {/* Ask button */}
      {!explanation && !loading && (
        <div style={{ padding: '12px' }}>
          <button
            className="btn-primary"
            style={{ width: '100%' }}
            onClick={() => fetchExplanation(level)}
          >
            Ask AI to explain
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ padding: '16px', color: 'var(--text-muted)', fontSize: '12px', textAlign: 'center' }}>
          ⏳ Asking Groq…
        </div>
      )}

      {/* Error */}
      {error && (
        <div style={{ padding: '12px', color: '#f87171', fontSize: '12px' }}>
          ⚠ {error}
        </div>
      )}

      {/* Explanation */}
      {explanation && !loading && (
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '12px',
            fontSize: '12px',
            lineHeight: 1.6,
          }}
        >
          {tab === 'technical' ? (
            <ReactMarkdown>{explanation}</ReactMarkdown>
          ) : (
            <ReactMarkdown>
              {`*Here's an analogy to help you understand:*\n\n${explanation}`}
            </ReactMarkdown>
          )}
        </div>
      )}
    </div>
  )
}
