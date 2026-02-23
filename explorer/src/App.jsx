import React, { useCallback, useEffect, useState, useRef, useMemo } from 'react';
import { ReactFlowProvider, useNodesState, useEdgesState, addEdge } from 'reactflow';
import 'reactflow/dist/style.css';

import GraphViewer from './components/GraphViewer';
import ExplanationPanel from './components/ExplanationPanel';
import FileSidebar from './components/FileSidebar';
import CodePanel from './components/CodePanel';
import SearchBar from './components/SearchBar';
import ChatDrawer from './components/ChatDrawer';
import LearningPath from './components/LearningPath';
import ProjectUpload from './components/ProjectUpload';
import SimulationControls from './components/SimulationControls';
import { getLayoutedElements } from './utils/layout';

const TRAIL_LENGTH = 4;

function AppInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // All graph data (unfiltered)
  const [allNodes, setAllNodes] = useState([]);
  const [allEdges, setAllEdges] = useState([]);

  // File selection
  const [selectedFile, setSelectedFile] = useState(null);

  // Refs for Game Loop
  const nodesRef = useRef([]);
  const edgesRef = useRef([]);
  const activeNodeIdRef = useRef(null);
  const trailRef = useRef([]);

  useEffect(() => { nodesRef.current = nodes; }, [nodes]);
  useEffect(() => { edgesRef.current = edges; }, [edges]);

  const [selectedNode, setSelectedNode] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);

  // Ghost Runner State
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeNodeId, setActiveNodeId] = useState(null);
  const [stepCount, setStepCount] = useState(0);
  const [speed, setSpeed] = useState(2500);
  const [currentLabel, setCurrentLabel] = useState('');

  // Code Panel state
  const [codePanelOpen, setCodePanelOpen] = useState(true);
  const [codePanelNode, setCodePanelNode] = useState(null);

  // New component states
  const [chatOpen, setChatOpen] = useState(false);
  const [learningPathOpen, setLearningPathOpen] = useState(false);

  useEffect(() => { activeNodeIdRef.current = activeNodeId; }, [activeNodeId]);

  // Load graph data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/graph_data.json');
        if (!response.ok) return;
        const data = await response.json();

        const customNodes = data.nodes.map(n => ({
          ...n,
          type: 'custom',
          data: {
            ...n.data,
            file: n.data.file || n.data.original_data?.file || null,
            lineno: n.data.lineno || n.data.original_data?.lineno,
            entry_point: n.data.entry_point || false,
          }
        }));

        setAllNodes(customNodes);
        setAllEdges(data.edges);

        // Auto-select first file that has an entry point, or just the first file
        const filesSet = new Set();
        let entryFile = null;
        customNodes.forEach(n => {
          const f = n.data.file;
          if (f) {
            filesSet.add(f);
            if (n.data.entry_point && !entryFile) entryFile = f;
          }
        });
        setSelectedFile(entryFile || [...filesSet][0] || null);

      } catch (error) {
        console.error("Failed to fetch graph data:", error);
      }
    };
    fetchData();
  }, []);

  // Compute file list and stats
  const { files, nodeStats } = useMemo(() => {
    const statsMap = {};
    allNodes.forEach(n => {
      const f = n.data?.file || '_external';
      if (!statsMap[f]) statsMap[f] = { count: 0, hasEntry: false, types: {} };
      statsMap[f].count++;
      if (n.data?.entry_point) statsMap[f].hasEntry = true;
      const t = n.data?.type || 'default';
      statsMap[f].types[t] = (statsMap[f].types[t] || 0) + 1;
    });

    const fileList = Object.keys(statsMap).sort((a, b) => {
      if (statsMap[a].hasEntry && !statsMap[b].hasEntry) return -1;
      if (!statsMap[a].hasEntry && statsMap[b].hasEntry) return 1;
      return a.localeCompare(b);
    });

    return { files: fileList, nodeStats: statsMap };
  }, [allNodes]);

  const handleUploadSuccess = useCallback((result) => {
    const { nodes: newNodes, edges: newEdges } = result;

    // Process nodes to match the "custom" type and add metadata
    const customNodes = newNodes.map(n => ({
      ...n,
      type: 'custom',
      data: {
        ...n.data,
        file: n.data.file || n.data.original_data?.file || null,
        lineno: n.data.lineno || n.data.original_data?.lineno,
        entry_point: n.data.entry_point || false,
      }
    }));

    // Auto-select the first file from the new project
    const filesSet = new Set();
    customNodes.forEach(n => {
      if (n.data.file) filesSet.add(n.data.file);
    });

    const newFiles = [...filesSet];
    if (newFiles.length > 0) {
      setSelectedFile(newFiles[0]);
    }

    setAllNodes(customNodes);
    setAllEdges(newEdges);

    // Reset UI state
    setSelectedNode(null);
    setExplanation(null);
    setIsPlaying(false);
    setActiveNodeId(null);
  }, [setNodes, setEdges, setAllNodes, setAllEdges, setSelectedFile, setSelectedNode, setExplanation, setIsPlaying, setActiveNodeId]);

  // Filter nodes/edges when file selection changes
  useEffect(() => {
    if (!selectedFile || allNodes.length === 0) return;

    setIsPlaying(false);
    setActiveNodeId(null);
    setStepCount(0);
    setCurrentLabel('');
    trailRef.current = [];

    const fileNodeIds = new Set();
    const fileNodes = allNodes.filter(n => {
      const nFile = n.data?.file || '_external';
      if (nFile === selectedFile) {
        fileNodeIds.add(n.id);
        return true;
      }
      return false;
    });

    const relevantEdges = allEdges.filter(e =>
      fileNodeIds.has(e.source) || fileNodeIds.has(e.target)
    );

    const externalNodeIds = new Set();
    relevantEdges.forEach(e => {
      if (!fileNodeIds.has(e.source)) externalNodeIds.add(e.source);
      if (!fileNodeIds.has(e.target)) externalNodeIds.add(e.target);
    });

    const externalNodes = allNodes
      .filter(n => externalNodeIds.has(n.id))
      .map(n => ({
        ...n,
        className: 'external-ref',
        data: { ...n.data, isExternal: true },
      }));

    const combinedNodes = [...fileNodes, ...externalNodes];

    const styledEdges = relevantEdges.map(e => {
      const isInternal = fileNodeIds.has(e.source) && fileNodeIds.has(e.target);
      return {
        ...e,
        style: isInternal
          ? { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 }
          : { stroke: 'rgba(148, 163, 184, 0.25)', strokeWidth: 2, strokeDasharray: '6 4' },
        animated: false,
        className: isInternal ? '' : 'external-edge',
      };
    });

    const layouted = getLayoutedElements(
      combinedNodes.map(n => ({ ...n })),
      styledEdges
    );

    setNodes(layouted.nodes);
    setEdges(layouted.edges);
  }, [selectedFile, allNodes, allEdges]);

  // Ghost Runner Loop
  useEffect(() => {
    let timeoutId;

    const tick = () => {
      if (!isPlaying) return;

      const currentNodes = nodesRef.current;
      const currentEdges = edgesRef.current;
      const currentActiveId = activeNodeIdRef.current;
      const trail = trailRef.current;

      if (currentNodes.length === 0) return;

      const currentNode = currentActiveId ? currentNodes.find(n => n.id === currentActiveId) : null;
      let nextNodeId;

      const pickRandom = (candidates) => {
        const withFile = candidates.filter(n => n.data?.file);
        const pool = withFile.length > 0 ? withFile : candidates;
        return pool[Math.floor(Math.random() * pool.length)];
      };

      if (!currentNode) {
        const picked = pickRandom(currentNodes);
        nextNodeId = picked?.id;
      } else {
        const connectedEdges = currentEdges.filter(e => e.source === currentActiveId);
        if (connectedEdges.length > 0) {
          const targetNodes = connectedEdges
            .map(e => currentNodes.find(n => n.id === e.target))
            .filter(Boolean);
          const withFile = targetNodes.filter(n => n.data?.file);
          const pool = withFile.length > 0 ? withFile : targetNodes;
          const picked = pool[Math.floor(Math.random() * pool.length)];
          nextNodeId = picked?.id;
        } else {
          const picked = pickRandom(currentNodes);
          nextNodeId = picked?.id;
        }
      }

      const newTrail = [nextNodeId, ...trail.filter(id => id !== nextNodeId)].slice(0, TRAIL_LENGTH);
      trailRef.current = newTrail;

      setActiveNodeId(nextNodeId);
      setStepCount(prev => prev + 1);

      const nextNode = currentNodes.find(n => n.id === nextNodeId);
      setCurrentLabel(nextNode?.data?.label || '');

      if (nextNode && nextNode.data?.file) {
        setCodePanelNode(nextNode);
      }

      setNodes(nds => nds.map(node => {
        const trailIndex = newTrail.indexOf(node.id);
        let className = node.data?.isExternal ? 'external-ref' : '';
        if (trailIndex === 0) className += ' ghost-active';
        else if (trailIndex === 1) className += ' ghost-trail-1';
        else if (trailIndex === 2) className += ' ghost-trail-2';
        else if (trailIndex >= 3) className += ' ghost-trail-3';
        return { ...node, className: className.trim() };
      }));

      if (currentActiveId && nextNodeId) {
        const trailEdgePairs = [];
        for (let i = 0; i < newTrail.length - 1; i++) {
          trailEdgePairs.push({ from: newTrail[i + 1], to: newTrail[i] });
        }

        setEdges(eds => eds.map(edge => {
          const isActive = edge.source === currentActiveId && edge.target === nextNodeId;
          const isTrail = trailEdgePairs.some(p => edge.source === p.from && edge.target === p.to);

          let className = '';
          let style = { stroke: 'rgba(148, 163, 184, 0.55)', strokeWidth: 3.5 };
          let animated = false;

          if (isActive) {
            className = 'ghost-edge-active';
            style = { stroke: '#f43f5e', strokeWidth: 7 };
            animated = true;
          } else if (isTrail) {
            className = 'ghost-edge-trail';
            style = { stroke: 'rgba(244, 63, 94, 0.5)', strokeWidth: 4 };
          }

          return { ...edge, className, style, animated };
        }));
      }

      timeoutId = setTimeout(tick, speed);
    };

    if (isPlaying && nodesRef.current.length > 0) {
      tick();
    }

    return () => clearTimeout(timeoutId);
  }, [isPlaying, speed]);

  // Reset visuals when stopping
  useEffect(() => {
    if (!isPlaying) {
      setNodes(nds => nds.map(n => ({
        ...n,
        className: n.data?.isExternal ? 'external-ref' : ''
      })));
      setEdges(eds => eds.map(e => ({
        ...e, animated: false,
        className: e.className?.includes('external-edge') ? 'external-edge' : '',
        style: e.className?.includes('external-edge')
          ? { stroke: 'rgba(148, 163, 184, 0.2)', strokeWidth: 1.5, strokeDasharray: '5 3' }
          : { stroke: 'rgba(148, 163, 184, 0.5)', strokeWidth: 2.5 }
      })));
    }
  }, [isPlaying]);

  const onResetSimulation = useCallback(() => {
    setIsPlaying(false);
    setActiveNodeId(null);
    setStepCount(0);
    setCurrentLabel('');
    trailRef.current = [];
  }, []);

  const handleSelectNode = useCallback((node) => {
    setSelectedNode(node);
    setCodePanelNode(node);
  }, []);

  const onNodeClick = useCallback(async (event, node) => {
    handleSelectNode(node);
    setExplanation(null);
    setLoading(true);
    fetchExplanation(node, 'technical', 'intermediate');
  }, []);

  const fetchExplanation = useCallback(async (node, type = 'technical', level = 'intermediate') => {
    setLoading(true);
    try {
      const file_path = node.data.file || node.data.original_data?.file;
      const payload = {
        file_path: file_path || null,
        node_id: node.id,
        type,
        level
      };

      const response = await fetch('http://localhost:8000/api/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      setExplanation(data.explanation ? data : "No explanation returned.");
    } catch (err) {
      console.error(err);
      setExplanation("Failed to connect to Vibe Teacher (Backend). Is server.py running?");
    } finally {
      setLoading(false);
    }
  }, []);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh' }}>
      {/* Sidebar */}
      <FileSidebar
        files={files}
        selectedFile={selectedFile}
        onSelectFile={setSelectedFile}
        nodeStats={nodeStats}
      />

      {/* Main Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        <div className="vibe-header">
          <h1>⚡ Vibe Learning</h1>
          <span className="status-badge">AI Active</span>
          {selectedFile && (
            <span className="current-file-badge">
              📄 {selectedFile.split(/[/\\]/).pop()}
            </span>
          )}
          <button
            className="header-action-btn"
            onClick={() => setLearningPathOpen(true)}
            title="Learning Path"
          >
            🎯 Learn
          </button>

          <ProjectUpload onUploadSuccess={handleUploadSuccess} />

          <SearchBar
            allNodes={allNodes}
            onSelectNode={handleSelectNode}
            onSelectFile={setSelectedFile}
          />
        </div>

        {/* Graph */}
        <div style={{ flex: 1, position: 'relative' }}>
          <GraphViewer
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
          />

          <SimulationControls
            isPlaying={isPlaying}
            onToggle={() => setIsPlaying(!isPlaying)}
            onReset={onResetSimulation}
            stepCount={stepCount}
            speed={speed}
            onSpeedChange={setSpeed}
            currentLabel={currentLabel}
          />

          <ExplanationPanel
            node={selectedNode}
            explanation={explanation}
            loading={loading}
            onClose={() => setSelectedNode(null)}
            fetchExplanation={fetchExplanation}
          />

          {/* Chat Drawer */}
          <ChatDrawer
            selectedNode={selectedNode}
            isOpen={chatOpen}
            onToggle={() => setChatOpen(!chatOpen)}
          />
        </div>

        {/* Code Panel — Bottom */}
        <CodePanel
          activeNode={codePanelNode}
          isGhostRunning={isPlaying}
          isOpen={codePanelOpen}
          onToggle={() => setCodePanelOpen(!codePanelOpen)}
        />
      </div>

      {/* Learning Path Overlay */}
      <LearningPath
        selectedFile={selectedFile}
        allNodes={allNodes}
        onSelectNode={handleSelectNode}
        onSelectFile={setSelectedFile}
        isOpen={learningPathOpen}
        onToggle={() => setLearningPathOpen(false)}
      />
    </div>
  );
}

// Wrap with ReactFlowProvider so SearchBar and LearningPath can use useReactFlow()
export default function App() {
  return (
    <ReactFlowProvider>
      <AppInner />
    </ReactFlowProvider>
  );
}
