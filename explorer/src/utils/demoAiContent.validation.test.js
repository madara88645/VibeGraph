// explorer/src/utils/demoAiContent.validation.test.js
import { describe, it, expect } from 'vitest';
import graph from '../../public/demo_graph_data.json';
import ai from '../../public/demo_ai_content.json';

const LEVELS = ['beginner', 'intermediate', 'advanced'];

describe('demo_ai_content.json', () => {
  it('has an explanation entry (snippet + 3 levels) for every demo node', () => {
    const nodeIds = graph.nodes.map((n) => n.id);
    for (const id of nodeIds) {
      const entry = ai.explanations[id];
      expect(entry, `missing explanation for node ${id}`).toBeTruthy();
      expect(typeof entry.snippet).toBe('string');
      for (const level of LEVELS) {
        const detail = entry.levels?.[level];
        expect(detail, `missing ${level} for ${id}`).toBeTruthy();
        expect(detail.analogy.trim().length).toBeGreaterThan(0);
        expect(detail.technical.trim().length).toBeGreaterThan(0);
        expect(detail.key_takeaway.trim().length).toBeGreaterThan(0);
      }
    }
  });

  it('only references node ids that exist in the demo graph from chat', () => {
    const nodeIds = new Set(graph.nodes.map((n) => n.id));
    for (const qa of ai.chat) {
      expect(nodeIds.has(qa.nodeId), `chat references unknown node ${qa.nodeId}`).toBe(true);
      expect(qa.question.trim().length).toBeGreaterThan(0);
      expect(qa.answer.trim().length).toBeGreaterThan(0);
    }
  });
});
