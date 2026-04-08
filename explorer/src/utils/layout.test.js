import { describe, it, expect } from 'vitest';
import { getLayoutedElements } from './layout';

describe('getLayoutedElements', () => {
    it('returns nodes with position properties', () => {
        const nodes = [
            { id: 'a', position: { x: 0, y: 0 } },
            { id: 'b', position: { x: 0, y: 0 } },
        ];
        const edges = [{ source: 'a', target: 'b' }];

        const result = getLayoutedElements(nodes, edges);

        expect(result.nodes).toHaveLength(2);
        result.nodes.forEach((node) => {
            expect(node.position).toBeDefined();
            expect(typeof node.position.x).toBe('number');
            expect(typeof node.position.y).toBe('number');
        });
    });

    it('returns empty arrays for empty input', () => {
        const result = getLayoutedElements([], []);
        expect(result.nodes).toEqual([]);
        expect(result.edges).toEqual([]);
    });

    it('handles nodes with no edges', () => {
        const nodes = [
            { id: 'x', position: { x: 0, y: 0 } },
            { id: 'y', position: { x: 0, y: 0 } },
        ];
        const edges = [];

        const result = getLayoutedElements(nodes, edges);

        expect(result.nodes).toHaveLength(2);
        result.nodes.forEach((node) => {
            expect(node.position.x).toBeDefined();
            expect(node.position.y).toBeDefined();
        });
    });

    it('sets targetPosition and sourcePosition on nodes', () => {
        const nodes = [{ id: 'n1', position: { x: 0, y: 0 } }];
        const edges = [];

        const result = getLayoutedElements(nodes, edges);

        expect(result.nodes[0].targetPosition).toBe('top');
        expect(result.nodes[0].sourcePosition).toBe('bottom');
    });

    it('returns both nodes and edges in result', () => {
        const nodes = [
            { id: '1', position: { x: 0, y: 0 } },
            { id: '2', position: { x: 0, y: 0 } },
        ];
        const edges = [{ source: '1', target: '2' }];

        const result = getLayoutedElements(nodes, edges);

        expect(result).toHaveProperty('nodes');
        expect(result).toHaveProperty('edges');
        expect(result.edges).toEqual(edges);
    });

    it('lays out connected nodes at different y positions (top-to-bottom)', () => {
        const nodes = [
            { id: 'parent', position: { x: 0, y: 0 } },
            { id: 'child', position: { x: 0, y: 0 } },
        ];
        const edges = [{ source: 'parent', target: 'child' }];

        const result = getLayoutedElements(nodes, edges);

        const parentNode = result.nodes.find((n) => n.id === 'parent');
        const childNode = result.nodes.find((n) => n.id === 'child');

        // In TB layout, parent should be above child (smaller y)
        expect(parentNode.position.y).toBeLessThan(childNode.position.y);
    });

    it('ignores edges referencing nodes not in the set', () => {
        const nodes = [{ id: 'a', position: { x: 0, y: 0 } }];
        const edges = [{ source: 'a', target: 'missing' }];

        const result = getLayoutedElements(nodes, edges);

        expect(result.nodes).toHaveLength(1);
        expect(result.nodes[0].position).toBeDefined();
    });

    it('handles a larger graph with multiple levels', () => {
        const nodes = [
            { id: 'entry', position: { x: 0, y: 0 } },
            { id: 'mid1', position: { x: 0, y: 0 } },
            { id: 'mid2', position: { x: 0, y: 0 } },
            { id: 'leaf', position: { x: 0, y: 0 } },
        ];
        const edges = [
            { source: 'entry', target: 'mid1' },
            { source: 'entry', target: 'mid2' },
            { source: 'mid1', target: 'leaf' },
        ];

        const result = getLayoutedElements(nodes, edges);

        expect(result.nodes).toHaveLength(4);
        // All nodes should have valid positions
        result.nodes.forEach((node) => {
            expect(Number.isFinite(node.position.x)).toBe(true);
            expect(Number.isFinite(node.position.y)).toBe(true);
        });
    });
});
