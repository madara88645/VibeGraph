import React, { useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import CustomNode from './CustomNode.jsx'

const nodeTypes = { custom: CustomNode }

function edgeStyle(edge, ghostTrail) {
  const isTrail = ghostTrail.includes(edge.id)
  return {
    ...edge,
    animated: isTrail,
    style: {
      stroke: edge.data?.crossFile ? 'var(--accent-class)' : 'var(--accent-fn)',
      strokeWidth: isTrail ? 3 : 1.5,
      strokeDasharray: edge.data?.crossFile ? '5,4' : undefined,
      filter: isTrail ? 'drop-shadow(0 0 4px var(--accent-fn))' : undefined,
    },
  }
}

export default function GraphViewer({
  nodes,
  edges,
  ghostTrail,
  onNodeClick,
}) {
  const [rfNodes, , onNodesChange] = useNodesState(nodes)
  const [rfEdges, , onEdgesChange] = useEdgesState(edges)

  const styledEdges = rfEdges.map((e) => edgeStyle(e, ghostTrail))

  const handleNodeClick = useCallback(
    (_evt, node) => onNodeClick && onNodeClick(node),
    [onNodeClick]
  )

  return (
    <div style={{ flex: 1, height: '100%' }}>
      <ReactFlow
        nodes={rfNodes}
        edges={styledEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="var(--border)" gap={24} />
        <Controls />
        <MiniMap
          nodeColor={(n) => {
            const colors = {
              function: '#00d4ff',
              class: '#a855f7',
              entry: '#22c55e',
            }
            return colors[n.data?.nodeType] ?? '#888'
          }}
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
        />
      </ReactFlow>
    </div>
  )
}
