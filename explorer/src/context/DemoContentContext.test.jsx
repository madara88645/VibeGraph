import { describe, it, expect } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { DemoContentProvider, useDemoContent } from './DemoContentContext';

const wrapper = ({ children }) => <DemoContentProvider>{children}</DemoContentProvider>;

const SAMPLE = {
  explanations: {
    foo: {
      snippet: 'def foo(): pass',
      levels: {
        beginner: { analogy: 'a', technical: 't', key_takeaway: 'k' },
        intermediate: { analogy: 'a2', technical: 't2', key_takeaway: 'k2' },
        advanced: { analogy: 'a3', technical: 't3', key_takeaway: 'k3' },
      },
    },
  },
  chat: [{ nodeId: 'foo', question: 'What does foo do?', answer: 'Nothing.' }],
};

describe('DemoContentContext', () => {
  it('defaults to not-demo with empty accessors', () => {
    const { result } = renderHook(() => useDemoContent(), { wrapper });
    expect(result.current.isDemo).toBe(false);
    expect(result.current.getBakedExplanation('foo', 'beginner')).toBeNull();
    expect(result.current.getCannedChats('foo')).toEqual([]);
  });

  it('returns the full /api/explain response shape for a baked node+level', () => {
    const { result } = renderHook(() => useDemoContent(), { wrapper });
    act(() => result.current.setDemoContent(SAMPLE));
    expect(result.current.isDemo).toBe(true);
    expect(result.current.getBakedExplanation('foo', 'beginner')).toEqual({
      node_id: 'foo',
      explanation: { analogy: 'a', technical: 't', key_takeaway: 'k' },
      snippet: 'def foo(): pass',
    });
  });

  it('returns canned chats for a node and clears on demand', () => {
    const { result } = renderHook(() => useDemoContent(), { wrapper });
    act(() => result.current.setDemoContent(SAMPLE));
    expect(result.current.getCannedChats('foo')).toEqual([
      { nodeId: 'foo', question: 'What does foo do?', answer: 'Nothing.' },
    ]);
    act(() => result.current.clearDemoContent());
    expect(result.current.isDemo).toBe(false);
    expect(result.current.getBakedExplanation('foo', 'beginner')).toBeNull();
  });
});
