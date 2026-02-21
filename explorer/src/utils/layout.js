/**
 * Dynamic Call-Graph Layout
 * 
 * Uses dagre to position nodes based on their actual call relationships.
 * Since we now filter per-file (5-15 nodes), dagre runs instantly
 * and produces a natural top-to-bottom call flow:
 *   entry_point → callers → callees → leaf functions
 * 
 * This makes the graph look like actual code execution flow.
 */

import dagre from 'dagre';

const NODE_W = 210;
const NODE_H = 65;

export const getLayoutedElements = (nodes, edges) => {
    if (nodes.length === 0) return { nodes, edges };

    const g = new dagre.graphlib.Graph();
    g.setDefaultEdgeLabel(() => ({}));
    g.setGraph({
        rankdir: 'TB',       // top → bottom (like code execution)
        ranksep: 100,        // vertical gap between call levels
        nodesep: 60,         // horizontal gap between siblings
        edgesep: 30,
        marginx: 40,
        marginy: 40,
    });

    // Add nodes
    nodes.forEach(node => {
        g.setNode(node.id, { width: NODE_W, height: NODE_H });
    });

    // Add edges (only those connecting nodes in our set)
    const nodeIds = new Set(nodes.map(n => n.id));
    edges.forEach(edge => {
        if (nodeIds.has(edge.source) && nodeIds.has(edge.target)) {
            g.setEdge(edge.source, edge.target);
        }
    });

    // Run layout
    dagre.layout(g);

    // Apply positions
    nodes.forEach(node => {
        const pos = g.node(node.id);
        if (pos) {
            node.position = {
                x: pos.x - NODE_W / 2,
                y: pos.y - NODE_H / 2,
            };
        } else {
            // Orphan node — place at end
            node.position = { x: 0, y: nodes.length * (NODE_H + 20) };
        }
        node.targetPosition = 'top';
        node.sourcePosition = 'bottom';
    });

    return { nodes, edges };
};
