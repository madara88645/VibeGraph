import { describe, expect, it } from 'vitest';

import { buildNodeGroundingContext } from './graphContext';

describe('buildNodeGroundingContext', () => {
  it('returns empty result when nodeId is falsy', () => {
    const context = buildNodeGroundingContext({
      nodeId: null,
      allNodes: [{ id: 'a' }, { id: 'b' }],
      allEdges: [{ source: 'a', target: 'b' }],
    });

    expect(context).toEqual({ callers: [], callees: [], neighbors: [] });
  });

  it('returns empty arrays when there are no nodes or edges', () => {
    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes: [], allEdges: [] });

    expect(context).toEqual({ callers: [], callees: [], neighbors: [] });
  });

  it('finds callers and callees from edges touching the node', () => {
    const allNodes = [{ id: 'a' }, { id: 'b' }, { id: 'c' }];
    const allEdges = [
      { source: 'b', target: 'a' },
      { source: 'a', target: 'c' },
    ];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context.callers).toEqual(['b']);
    expect(context.callees).toEqual(['c']);
    expect(context.neighbors).toEqual(['b', 'c']);
  });

  it('treats a self-loop as both a caller and a callee', () => {
    const allNodes = [{ id: 'a' }];
    const allEdges = [{ source: 'a', target: 'a' }];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context.callers).toEqual(['a']);
    expect(context.callees).toEqual(['a']);
    expect(context.neighbors).toEqual(['a']);
  });

  it('dedupes duplicate edges between the same pair of nodes', () => {
    const allNodes = [{ id: 'a' }, { id: 'b' }];
    const allEdges = [
      { source: 'b', target: 'a' },
      { source: 'b', target: 'a' },
    ];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context.callers).toEqual(['b']);
  });

  it('ignores edges referencing a node id that is not in allNodes', () => {
    const allNodes = [{ id: 'a' }];
    const allEdges = [{ source: 'ghost', target: 'a' }];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context.callers).toEqual([]);
    expect(context.neighbors).toEqual([]);
  });

  it('skips edges missing a source or target', () => {
    const allNodes = [{ id: 'a' }, { id: 'b' }];
    const allEdges = [{ source: undefined, target: 'a' }, { source: 'b' }, {}];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context).toEqual({ callers: [], callees: [], neighbors: [] });
  });

  it('returns only callers when the node has no outgoing edges', () => {
    const allNodes = [{ id: 'a' }, { id: 'b' }];
    const allEdges = [{ source: 'b', target: 'a' }];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context.callers).toEqual(['b']);
    expect(context.callees).toEqual([]);
  });

  it('returns only callees when the node has no incoming edges', () => {
    const allNodes = [{ id: 'a' }, { id: 'b' }];
    const allEdges = [{ source: 'a', target: 'b' }];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context.callers).toEqual([]);
    expect(context.callees).toEqual(['b']);
  });

  it('handles large fan-in and fan-out without duplicates', () => {
    const allNodes = [{ id: 'a' }, ...Array.from({ length: 20 }, (_, i) => ({ id: `n${i}` }))];
    const allEdges = [
      ...Array.from({ length: 20 }, (_, i) => ({ source: `n${i}`, target: 'a' })),
      ...Array.from({ length: 20 }, (_, i) => ({ source: 'a', target: `n${i}` })),
    ];

    const context = buildNodeGroundingContext({ nodeId: 'a', allNodes, allEdges });

    expect(context.callers).toHaveLength(20);
    expect(context.callees).toHaveLength(20);
    expect(context.neighbors).toHaveLength(20);
  });
});
