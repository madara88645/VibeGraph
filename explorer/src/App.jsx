import React, { useState, useEffect, useRef, useCallback } from 'react'
import GraphViewer from './components/GraphViewer.jsx'
import FileSidebar from './components/FileSidebar.jsx'
import CodePanel from './components/CodePanel.jsx'
import SimulationControls from './components/SimulationControls.jsx'
import ExplanationPanel from './components/ExplanationPanel.jsx'
import { applyDagreLayout } from './utils/layout.js'

const TRAIL_LENGTH = 4   // Ghost Runner trail size

export default function App() {
  const [rawData, setRawData] = useState(null)
  const [activeFile, setActiveFile] = useState(null)
  const [activeNode, setActiveNode] = useState(null)
  const [showExplanation, setShowExplanation] = useState(false)

  // Ghost Runner state
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [step, setStep] = useState(0)
  const [traversal, setTraversal] = useState([])   // ordered node ids
  const timerRef = useRef(null)

  // ------------------------------------------------------------------
  // Load graph data
  // ------------------------------------------------------------------
  useEffect(() => {
    fetch('/graph_data.json')
      .then((r) => r.json())
      .then((data) => setRawData(data))
      .catch(() =>
        setRawData({ nodes: [], edges: [] })
      )
  }, [])

  // ------------------------------------------------------------------
  // Derive layouted nodes/edges
  // ------------------------------------------------------------------
  const { nodes, edges } = React.useMemo(() => {
    if (!rawData) return { nodes: [], edges: [] }

    let visibleNodes = rawData.nodes
    let visibleEdges = rawData.edges

    if (activeFile) {
      const ownIds = new Set(
        rawData.nodes.filter((n) => n.data.file === activeFile).map((n) => n.id)
      )
      // Show own nodes fully; show referenced external nodes dimmed
      const referencedExternalIds = new Set()
      rawData.edges.forEach((e) => {
        if (ownIds.has(e.source) && !ownIds.has(e.target)) referencedExternalIds.add(e.target)
        if (ownIds.has(e.target) && !ownIds.has(e.source)) referencedExternalIds.add(e.source)
      })

      visibleNodes = rawData.nodes
        .filter((n) => ownIds.has(n.id) || referencedExternalIds.has(n.id))
        .map((n) => ({
          ...n,
          data: {
            ...n.data,
            dimmed: !ownIds.has(n.id),
          },
        }))

      const visibleIds = new Set(visibleNodes.map((n) => n.id))
      visibleEdges = rawData.edges.filter(
        (e) => visibleIds.has(e.source) && visibleIds.has(e.target)
      )
    }

    const { nodes: ln, edges: le } = applyDagreLayout(visibleNodes, visibleEdges)

    // Mark glowing nodes (Ghost Runner trail)
    const trailSet = new Set(ghostTrailIds())
    return {
      nodes: ln.map((n) => ({
        ...n,
        data: { ...n.data, glowing: trailSet.has(n.id) },
      })),
      edges: le,
    }
  }, [rawData, activeFile, step, traversal])  // eslint-disable-line react-hooks/exhaustive-deps

  // ------------------------------------------------------------------
  // Ghost Runner helpers
  // ------------------------------------------------------------------
  function ghostTrailIds() {
    if (traversal.length === 0) return []
    const start = Math.max(0, step - TRAIL_LENGTH + 1)
    return traversal.slice(start, step + 1)
  }

  function ghostTrailEdgeIds() {
    const ids = ghostTrailIds()
    const edgeIds = []
    for (let i = 0; i < ids.length - 1; i++) {
      edgeIds.push(`${ids[i]}->${ids[i + 1]}`)
    }
    return edgeIds
  }

  // Build traversal order from edges (simple BFS from entry nodes)
  function buildTraversal(nodes, edges) {
    const entryNodes = nodes.filter((n) => n.data.nodeType === 'entry')
    const starts = entryNodes.length > 0 ? entryNodes : nodes.slice(0, 1)
    const adjacency = {}
    edges.forEach((e) => {
      if (!adjacency[e.source]) adjacency[e.source] = []
      adjacency[e.source].push(e.target)
    })

    const visited = new Set()
    const order = []
    const queue = starts.map((n) => n.id)

    while (queue.length > 0) {
      const id = queue.shift()
      if (visited.has(id)) continue
      visited.add(id)
      order.push(id)
      if (adjacency[id]) queue.push(...adjacency[id])
    }
    // Add any disconnected nodes
    nodes.forEach((n) => {
      if (!visited.has(n.id)) order.push(n.id)
    })
    return order
  }

  // ------------------------------------------------------------------
  // Simulation controls
  // ------------------------------------------------------------------
  const handlePlay = useCallback(() => {
    if (traversal.length === 0 && rawData) {
      const t = buildTraversal(rawData.nodes, rawData.edges)
      setTraversal(t)
      setStep(0)
    }
    setIsPlaying(true)
  }, [traversal, rawData])

  const handlePause = useCallback(() => setIsPlaying(false), [])

  const handleReset = useCallback(() => {
    setIsPlaying(false)
    setStep(0)
    setTraversal([])
  }, [])

  useEffect(() => {
    if (!isPlaying) {
      clearInterval(timerRef.current)
      return
    }
    const interval = 1000 / speed
    timerRef.current = setInterval(() => {
      setStep((s) => {
        const next = s + 1
        if (next >= traversal.length) {
          setIsPlaying(false)
          return s
        }
        // Auto-follow active node
        const nodeId = traversal[next]
        const node = rawData?.nodes.find((n) => n.id === nodeId)
        if (node) setActiveNode(node)
        return next
      })
    }, interval)
    return () => clearInterval(timerRef.current)
  }, [isPlaying, speed, traversal, rawData])

  // ------------------------------------------------------------------
  // Node click
  // ------------------------------------------------------------------
  const handleNodeClick = useCallback((node) => {
    setActiveNode(node)
    setShowExplanation(true)
  }, [])

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  if (!rawData) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--text-muted)' }}>
        Loading graph data…
      </div>
    )
  }

  const trailEdges = ghostTrailEdgeIds()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Top bar */}
      <header
        style={{
          padding: '8px 16px',
          background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 800, fontSize: '16px', color: 'var(--accent-fn)', letterSpacing: '0.04em' }}>
          VibeGraph
        </span>
        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
          {nodes.length} nodes · {edges.length} edges
        </span>
      </header>

      {/* Ghost Runner controls */}
      <SimulationControls
        isPlaying={isPlaying}
        speed={speed}
        onPlay={handlePlay}
        onPause={handlePause}
        onReset={handleReset}
        onSpeedChange={setSpeed}
        currentStep={step}
        totalSteps={traversal.length}
      />

      {/* Main area */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <FileSidebar
          nodes={rawData.nodes}
          activeFile={activeFile}
          onFileSelect={setActiveFile}
        />

        {/* Graph + Code Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
          <GraphViewer
            nodes={nodes}
            edges={edges}
            ghostTrail={trailEdges}
            onNodeClick={handleNodeClick}
          />
          <CodePanel activeNode={activeNode} />
        </div>

        {/* Explanation Panel */}
        {showExplanation && activeNode && (
          <ExplanationPanel
            activeNode={activeNode}
            onClose={() => setShowExplanation(false)}
          />
        )}
      </div>
    </div>
  )
}
