# Static Pre-Baked Demo AI Content — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the bundled demo graph show full-quality AI explanations and a guided Q&A with zero key, zero server cost, and zero live LLM calls, by serving hand-authored pre-baked content that is byte-compatible with the live `/api/explain` and `/api/chat` responses.

**Architecture:** A static `demo_ai_content.json` artifact (authored by Claude, no API) holds per-node snippets + per-level explanation objects + a few canned Q&A. A `DemoContentContext` holds it in memory (set on demo load, cleared on real upload, rehydrated on reload via a `source:'demo'` cache tag). Two interception points serve baked content before any network/key check: `useNodeInteraction.fetchExplanation` (explanations) and `ChatDrawer` (canned chat). The user's own uploaded project is untouched (stays BYOK).

**Tech Stack:** React (JSX), Vitest + @testing-library/react, Vite. Frontend only — no backend/prompt/deploy/dependency changes.

**Spec:** `docs/superpowers/specs/2026-06-25-static-demo-ai-content-design.md`

---

## ⚠️ Prerequisite — branch base (read first)

The local `main` in this checkout is **behind** `origin/main`: PR #479 (which created
`explorer/src/utils/loadDemoGraph.js`, the `handleLoadDemo` glue in `App.jsx`, and the
demo CTA in `GraphViewer.jsx`) was squash-merged on the remote, but local `main` was **not**
pulled (parallel-Codex shared-checkout rule). **This feature builds on top of #479.**

Before implementing, base the work branch on the #479-inclusive remote main:

```bash
git fetch origin
git switch -c feat/static-demo-ai-content-impl origin/main   # has #479
# (cherry-pick the spec commit if you want it on this branch:)
git cherry-pick 5427a36    # the docs(demo) spec commit, optional
```

Verify `explorer/src/utils/loadDemoGraph.js` exists before starting Task 2:
```bash
test -f explorer/src/utils/loadDemoGraph.js && echo OK || echo "MISSING — wrong base"
```
Expected: `OK`.

All file paths below assume the post-#479 tree.

---

## File Structure

**New files:**
- `explorer/public/demo_ai_content.json` — the static baked AI artifact (data).
- `explorer/src/context/DemoContentContext.jsx` — React context: holds baked content, exposes `isDemo` + accessors, set/clear.
- `explorer/src/context/DemoContentContext.test.jsx` — unit tests for the context.
- `explorer/src/utils/demoAiContent.validation.test.js` — no-key Vitest validator (coverage + schema).

**Modified files:**
- `explorer/src/utils/loadDemoGraph.js` — add `loadDemoAiContent()` (best-effort fetch of the artifact). `loadDemoGraph()` signature unchanged.
- `explorer/src/App.jsx` — wrap subtree in `DemoContentProvider`; in `handleLoadDemo` set baked content; pass `getBakedExplanation` to `useNodeInteraction` and `isDemo`/`getCannedChats` to `ChatDrawer`; clear baked content on real upload; rehydrate on reload.
- `explorer/src/hooks/useNodeInteraction.js` — baked-first short-circuit in `fetchExplanation`.
- `explorer/src/hooks/useGraphData.js` — `handleUploadSuccess` accepts a `source` arg; cache stores it; expose restored `source`.
- `explorer/src/components/ChatDrawer.jsx` — demo suggestion chips + demo wall.
- `explorer/src/components/ProjectUpload.jsx` — demo-load sets demo content / real upload clears it (via props).

**Artifact schema** (the contract every task relies on):
```jsonc
{
  "version": 1,
  "generatedAt": "2026-06-25",
  "author": "claude-authored (no live API call, no key)",
  "graphFile": "demo_graph_data.json",
  "explanations": {
    "<nodeId>": {
      "snippet": "<source code of the node, from app/demo_project/*.py>",
      "levels": {
        "beginner":     { "analogy": "…", "technical": "…(markdown)…", "key_takeaway": "…" },
        "intermediate": { "analogy": "…", "technical": "…(markdown)…", "key_takeaway": "…" },
        "advanced":     { "analogy": "…", "technical": "…(markdown)…", "key_takeaway": "…" }
      }
    }
  },
  "chat": [
    { "nodeId": "<id>", "question": "…", "answer": "…(markdown)…" }
  ]
}
```
Baked **explanation replay** reconstructs the full `/api/explain` response shape:
`{ node_id: <id>, explanation: explanations[id].levels[level], snippet: explanations[id].snippet }`.
Baked **chat replay** appends `{ role: 'assistant', content: chat[i].answer }`.

---

## Task 1: DemoContentContext + accessors

**Files:**
- Create: `explorer/src/context/DemoContentContext.jsx`
- Test: `explorer/src/context/DemoContentContext.test.jsx`

- [ ] **Step 1: Write the failing test**

```jsx
// explorer/src/context/DemoContentContext.test.jsx
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/context/DemoContentContext.test.jsx`
Expected: FAIL — `Failed to resolve import './DemoContentContext'`.

- [ ] **Step 3: Write minimal implementation**

```jsx
// explorer/src/context/DemoContentContext.jsx
import { createContext, useCallback, useContext, useMemo, useState } from 'react';

const DemoContentContext = createContext(null);

export function DemoContentProvider({ children }) {
  const [content, setContent] = useState(null);

  const setDemoContent = useCallback((next) => {
    setContent(next && typeof next === 'object' ? next : null);
  }, []);
  const clearDemoContent = useCallback(() => setContent(null), []);

  const getBakedExplanation = useCallback(
    (nodeId, level) => {
      const entry = content?.explanations?.[nodeId];
      const detail = entry?.levels?.[level];
      if (!entry || !detail) {
        return null;
      }
      return { node_id: nodeId, explanation: detail, snippet: entry.snippet ?? '' };
    },
    [content]
  );

  const getCannedChats = useCallback(
    (nodeId) => (content?.chat ?? []).filter((c) => c.nodeId === nodeId),
    [content]
  );

  const value = useMemo(
    () => ({
      isDemo: Boolean(content),
      setDemoContent,
      clearDemoContent,
      getBakedExplanation,
      getCannedChats,
    }),
    [content, setDemoContent, clearDemoContent, getBakedExplanation, getCannedChats]
  );

  return <DemoContentContext.Provider value={value}>{children}</DemoContentContext.Provider>;
}

export function useDemoContent() {
  const ctx = useContext(DemoContentContext);
  if (!ctx) {
    // Safe no-op shape so consumers work without a provider (e.g. isolated tests).
    return {
      isDemo: false,
      setDemoContent: () => {},
      clearDemoContent: () => {},
      getBakedExplanation: () => null,
      getCannedChats: () => [],
    };
  }
  return ctx;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd explorer && npx vitest run src/context/DemoContentContext.test.jsx`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add explorer/src/context/DemoContentContext.jsx explorer/src/context/DemoContentContext.test.jsx
git commit -m "feat(demo): DemoContentContext holding pre-baked AI content

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: `loadDemoAiContent()` — best-effort fetch of the artifact

**Files:**
- Modify: `explorer/src/utils/loadDemoGraph.js`
- Test: `explorer/src/utils/loadDemoGraph.test.js` (existing — add cases)

- [ ] **Step 1: Write the failing test** (append to the existing test file)

```js
// explorer/src/utils/loadDemoGraph.test.js  (add these cases)
import { loadDemoAiContent } from './loadDemoGraph';

describe('loadDemoAiContent', () => {
  it('fetches and returns the demo AI content', async () => {
    const payload = { version: 1, explanations: {}, chat: [] };
    const fetchSpy = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue({ ok: true, json: async () => payload });

    const result = await loadDemoAiContent();

    expect(fetchSpy).toHaveBeenCalledWith('/demo_ai_content.json');
    expect(result).toEqual(payload);
  });

  it('returns null (no throw) when the artifact is missing', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false, status: 404 });
    await expect(loadDemoAiContent()).resolves.toBeNull();
  });

  it('returns null (no throw) when fetch rejects', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('network down'));
    await expect(loadDemoAiContent()).resolves.toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/utils/loadDemoGraph.test.js -t loadDemoAiContent`
Expected: FAIL — `loadDemoAiContent is not a function` / import undefined.

- [ ] **Step 3: Write minimal implementation** (append to `loadDemoGraph.js`, do not change `loadDemoGraph`)

```js
// Loads the hand-authored, pre-baked demo AI content (explanations + canned chat)
// so the demo shows AI value with zero key and zero network to the AI endpoints.
// Best-effort: any failure returns null and the caller falls back to live/walled AI.
export async function loadDemoAiContent() {
    try {
        const res = await fetch('/demo_ai_content.json');
        if (!res.ok) {
            return null;
        }
        return await res.json();
    } catch {
        return null;
    }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd explorer && npx vitest run src/utils/loadDemoGraph.test.js`
Expected: PASS (existing cases + 3 new).

- [ ] **Step 5: Commit**

```bash
git add explorer/src/utils/loadDemoGraph.js explorer/src/utils/loadDemoGraph.test.js
git commit -m "feat(demo): loadDemoAiContent best-effort fetch of pre-baked AI artifact

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: `useGraphData` — carry a `source` through upload + cache

`handleUploadSuccess` currently hardcodes `source: GRAPH_CACHE_SOURCE` (`'user_upload'`).
Let it accept a `source` so demo loads tag the cache as `'demo'` (used by Task 8 rehydrate),
and expose the restored `source` so the app knows a restored graph is the demo.

**Files:**
- Modify: `explorer/src/hooks/useGraphData.js`
- Test: `explorer/src/hooks/useGraphData.test.jsx` (existing — add a case; create if absent)

- [ ] **Step 1: Write the failing test**

```jsx
// explorer/src/hooks/useGraphData.test.jsx  (add this case)
import { describe, it, expect, beforeEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useGraphData } from './useGraphData';

const DEMO_RESULT = {
  nodes: [{ id: 'n1', data: { file: 'a.py', entry_point: true } }],
  edges: [],
  meta: { truncated: false, total_nodes: 1, total_edges: 0, kept_nodes: 1, kept_edges: 0 },
};

describe('useGraphData source tagging', () => {
  beforeEach(() => localStorage.clear());

  it("stores source:'demo' in the graph cache when demo load passes source", () => {
    const { result } = renderHook(() => useGraphData());
    act(() => result.current.handleUploadSuccess(DEMO_RESULT, null, 'demo'));
    const cached = JSON.parse(localStorage.getItem(result.current.cacheKey));
    expect(cached.source).toBe('demo');
  });

  it("defaults to source:'user_upload' for a normal upload", () => {
    const { result } = renderHook(() => useGraphData());
    act(() => result.current.handleUploadSuccess(DEMO_RESULT));
    const cached = JSON.parse(localStorage.getItem(result.current.cacheKey));
    expect(cached.source).toBe('user_upload');
  });
});
```

> If `cacheKey` is not currently returned by the hook, expose it in the hook's return object
> (it is referenced internally as `cacheKey`). Add `cacheKey` to the returned object.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/hooks/useGraphData.test.jsx -t "source tagging"`
Expected: FAIL — cached.source is `'user_upload'` for the demo case (arg ignored).

- [ ] **Step 3: Write minimal implementation**

In `handleUploadSuccess` (line ~138), add the param and use it; keep the default:

```js
    const handleUploadSuccess = useCallback((result, resetGhostStateCallback, source = GRAPH_CACHE_SOURCE) => {
```

In the cache `payload` (line ~189) replace `source: GRAPH_CACHE_SOURCE,` with:

```js
                source,
```

Ensure `source` is in the `useCallback` deps array (line ~209) — it is a primitive arg, so no
dep change is needed; leave deps as-is.

If not already returned, add `cacheKey` to the hook's return object so callers/tests can read it.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd explorer && npx vitest run src/hooks/useGraphData.test.jsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add explorer/src/hooks/useGraphData.js explorer/src/hooks/useGraphData.test.jsx
git commit -m "feat(demo): thread a source tag through graph upload + cache

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Explanation interception in `useNodeInteraction`

Serve a baked explanation before the key/network path. The hook receives a
`getBakedExplanation` function via options (App wires it from `useDemoContent`).

**Files:**
- Modify: `explorer/src/hooks/useNodeInteraction.js`
- Test: `explorer/src/hooks/useNodeInteraction.test.jsx` (existing — add a case; create if absent)

- [ ] **Step 1: Write the failing test**

```jsx
// explorer/src/hooks/useNodeInteraction.test.jsx  (add this case)
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useNodeInteraction } from './useNodeInteraction';
import * as aiClient from '../utils/aiClient';

describe('useNodeInteraction baked demo explanations', () => {
  beforeEach(() => localStorage.clear());

  it('serves baked explanation without any network call or key', async () => {
    const fetchSpy = vi.spyOn(aiClient, 'fetchAiJson');
    const baked = {
      node_id: 'n1',
      explanation: { analogy: 'a', technical: 't', key_takeaway: 'k' },
      snippet: 'def n1(): pass',
    };
    const getBakedExplanation = vi.fn((id, level) =>
      id === 'n1' && level === 'intermediate' ? baked : null
    );

    const { result } = renderHook(() =>
      useNodeInteraction({ aiReady: false, getBakedExplanation })
    );

    await act(async () => {
      await result.current.fetchExplanation({ id: 'n1', data: {} }, 'technical', 'intermediate');
    });

    await waitFor(() => expect(result.current.explanation).toEqual(baked));
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/hooks/useNodeInteraction.test.jsx -t "baked demo"`
Expected: FAIL — with `aiReady:false` the hook returns the MISSING_KEY message instead of baked.

- [ ] **Step 3: Write minimal implementation**

Add `getBakedExplanation` to the hook options destructure (line ~34):

```js
export function useNodeInteraction({
  aiApiKey = '',
  selectedModel = '',
  aiReady = true,
  onRequireAiKey,
  onAuthError,
  onAuthCleared,
  allNodes = [],
  allEdges = [],
  getBakedExplanation = null,
} = {}) {
```

In `fetchExplanation`, immediately **after** the existing localStorage-cache block (the
`if (cached) { … return; }` ending at line ~78) and **before** the `ensureAiReady` gate (line ~80),
insert:

```js
      const baked = getBakedExplanation?.(node.id, level);
      if (baked) {
        explanationCacheRef.current.set(cacheKey, baked);
        setExplanation(baked);
        setLoading(false);
        return;
      }
```

Add `getBakedExplanation` to the `fetchExplanation` `useCallback` deps array (line ~138-147).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd explorer && npx vitest run src/hooks/useNodeInteraction.test.jsx`
Expected: PASS (existing + new).

- [ ] **Step 5: Commit**

```bash
git add explorer/src/hooks/useNodeInteraction.js explorer/src/hooks/useNodeInteraction.test.jsx
git commit -m "feat(demo): serve baked explanations before the key/network path

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Chat — demo suggestion chips + demo wall in `ChatDrawer`

In demo mode, render the selected node's canned questions as chips; clicking one appends the
question + baked answer with no network. Free-form input in demo (no key) shows an honest demo
wall instead of the generic missing-key message.

**Files:**
- Modify: `explorer/src/components/ChatDrawer.jsx`
- Test: `explorer/src/components/ChatDrawer.test.jsx` (existing — add cases; create if absent)

New props on `ChatDrawer`: `isDemo = false`, `getCannedChats = () => []`.

- [ ] **Step 1: Write the failing test**

```jsx
// explorer/src/components/ChatDrawer.test.jsx  (add these cases)
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatDrawer from './ChatDrawer';

const node = { id: 'n1', data: { file: 'a.py' } };

beforeEach(() => localStorage.clear());

describe('ChatDrawer demo mode', () => {
  it('shows canned question chips and replays the baked answer with no network', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, 'fetch');
    const getCannedChats = vi.fn(() => [
      { nodeId: 'n1', question: 'What does n1 do?', answer: 'It sums things.' },
    ]);

    render(
      <ChatDrawer
        selectedNode={node}
        allNodes={[node]}
        allEdges={[]}
        isOpen
        onToggle={() => {}}
        apiKey=""
        selectedModel=""
        aiReady={false}
        onOpenAiSettings={() => {}}
        isDemo
        getCannedChats={getCannedChats}
      />
    );

    const chip = await screen.findByRole('button', { name: /What does n1 do\?/i });
    await user.click(chip);

    expect(await screen.findByText('It sums things.')).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('shows the demo wall for a free-form question and makes no network call', async () => {
    const user = userEvent.setup();
    const fetchSpy = vi.spyOn(globalThis, 'fetch');

    render(
      <ChatDrawer
        selectedNode={node}
        allNodes={[node]}
        allEdges={[]}
        isOpen
        onToggle={() => {}}
        apiKey=""
        selectedModel=""
        aiReady={false}
        onOpenAiSettings={() => {}}
        isDemo
        getCannedChats={() => []}
      />
    );

    await user.type(screen.getByRole('textbox'), 'my own question');
    await user.keyboard('{Enter}');

    expect(await screen.findByText(/add a free OpenRouter key/i)).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/components/ChatDrawer.test.jsx -t "demo mode"`
Expected: FAIL — chips not rendered; free-form shows the generic missing-key message.

- [ ] **Step 3: Write minimal implementation**

Add the two props to the component signature (line ~25-35):

```js
const ChatDrawer = ({
  selectedNode,
  allNodes,
  allEdges,
  isOpen,
  onToggle,
  apiKey,
  selectedModel,
  aiReady,
  onOpenAiSettings,
  isDemo = false,
  getCannedChats = () => [],
}) => {
```

Add a constant near the other message constants (line ~16-23):

```js
const DEMO_FREEFORM_MESSAGE =
  'This is a live demo with sample answers. To ask your own questions or analyze your own code, add a free OpenRouter key.';
```

Add a handler that replays a canned answer with no network (place after `persistMessages`,
~line 81):

```js
  const sendCannedChat = useCallback(
    (qa) => {
      const next = [
        ...messages,
        { role: 'user', content: qa.question },
        { role: 'assistant', content: qa.answer },
      ];
      setMessages(next);
      persistMessages(next);
    },
    [messages, persistMessages]
  );
```

In `sendMessage`, intercept the demo free-form case **before** the existing `ensureAiReady`
block (line ~93). Insert at the top of `sendMessage`, right after the `if (!text || loading)`
guard (line ~91):

```js
    if (isDemo) {
      const next = [
        ...messages,
        { role: 'user', content: text },
        { role: 'assistant', content: DEMO_FREEFORM_MESSAGE },
      ];
      setMessages(next);
      persistMessages(next);
      setInputText('');
      return;
    }
```

Add `isDemo`, `persistMessages` to the `sendMessage` `useCallback` deps.

In the JSX, render the chips when in demo mode and the selected node has canned chats. Place
this just above the chat input row (find the input container in the render and insert before it):

```jsx
        {isDemo && getCannedChats(selectedNode?.id).length > 0 && (
          <div className="demo-chat-suggestions">
            {getCannedChats(selectedNode?.id).map((qa) => (
              <button
                key={qa.question}
                type="button"
                className="demo-chat-chip"
                onClick={() => sendCannedChat(qa)}
              >
                {qa.question}
              </button>
            ))}
          </div>
        )}
```

Add minimal styles to `explorer/src/index.css` (append near other chat styles):

```css
.demo-chat-suggestions { display: flex; flex-wrap: wrap; gap: 8px; padding: 8px 12px; }
.demo-chat-chip {
  font: inherit; font-size: 0.8rem; padding: 6px 12px; border-radius: 14px; cursor: pointer;
  color: var(--color-accent-primary); background: transparent;
  border: 1px solid rgba(16, 185, 129, 0.4); transition: background 0.2s ease;
}
.demo-chat-chip:hover { background: rgba(16, 185, 129, 0.08); }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd explorer && npx vitest run src/components/ChatDrawer.test.jsx`
Expected: PASS (existing + 2 new).

- [ ] **Step 5: Commit**

```bash
git add explorer/src/components/ChatDrawer.jsx explorer/src/index.css explorer/src/components/ChatDrawer.test.jsx
git commit -m "feat(demo): canned chat suggestion chips + honest demo wall

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Wire demo content in `App.jsx` + `ProjectUpload.jsx`

Wrap the app subtree in `DemoContentProvider`, set baked content on demo load, clear it on real
upload, and pass the accessors down to the hook (Task 4) and ChatDrawer (Task 5).

**Files:**
- Modify: `explorer/src/App.jsx`
- Modify: `explorer/src/components/ProjectUpload.jsx`
- Test: `explorer/src/App.test.jsx` (existing — add a case)

- [ ] **Step 1: Write the failing test**

```jsx
// explorer/src/App.test.jsx  (add this case; mock loadDemoAiContent alongside loadDemoGraph)
// At the top, extend the existing vi.mock('./utils/loadDemoGraph', ...) to also export loadDemoAiContent:
//   vi.mock('./utils/loadDemoGraph', () => ({
//     loadDemoGraph: vi.fn(),
//     loadDemoAiContent: vi.fn(),
//   }));
import { loadDemoGraph, loadDemoAiContent } from './utils/loadDemoGraph';

it('loads pre-baked AI content alongside the demo graph and serves a baked explanation', async () => {
  const user = userEvent.setup();
  loadDemoGraph.mockResolvedValue({ nodes: [{ id: 'n1', data: { file: 'a.py' } }], edges: [] });
  loadDemoAiContent.mockResolvedValue({
    explanations: {
      n1: {
        snippet: 'def n1(): pass',
        levels: {
          beginner: { analogy: 'a', technical: 't', key_takeaway: 'k' },
          intermediate: { analogy: 'a2', technical: 't2', key_takeaway: 'k2' },
          advanced: { analogy: 'a3', technical: 't3', key_takeaway: 'k3' },
        },
      },
    },
    chat: [],
  });

  render(<App />);
  await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledWith('/api/ai-config'));
  await user.click(screen.getByText('load-demo'));

  await waitFor(() => expect(loadDemoAiContent).toHaveBeenCalledTimes(1));
});
```

> This test reuses the existing `GraphViewer` mock (with the `load-demo` button) added in #479.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/App.test.jsx -t "pre-baked AI content"`
Expected: FAIL — `loadDemoAiContent` never called (App doesn't call it yet).

- [ ] **Step 3: Write minimal implementation**

In `App.jsx`:

1. Import the provider, hook, and the loader:
```js
import { DemoContentProvider, useDemoContent } from './context/DemoContentContext';
import { loadDemoGraph, loadDemoAiContent } from './utils/loadDemoGraph';
```
(Adjust the existing `loadDemoGraph` import to include `loadDemoAiContent`.)

2. Wrap the rendered tree. Find the top-level component that renders `AppInner` (or the App
export). Wrap it:
```jsx
export default function App() {
  return (
    <DemoContentProvider>
      <AppInner />
    </DemoContentProvider>
  );
}
```
(If `App` currently *is* `AppInner`, rename the inner to `AppInner` and add this wrapper.)

3. Inside `AppInner`, read the context:
```js
  const { isDemo, setDemoContent, clearDemoContent, getBakedExplanation, getCannedChats } =
    useDemoContent();
```

4. Update `handleLoadDemo` (added in #479) to also load + set baked content:
```js
  const handleLoadDemo = useCallback(async () => {
    try {
      const [data, ai] = await Promise.all([loadDemoGraph(), loadDemoAiContent()]);
      setDemoContent(ai);                 // ai may be null → context stays not-demo
      onUploadSuccess(data, undefined, 'demo');
      showToast('Demo project loaded successfully!', 'success');
    } catch (err) {
      showToast('Failed to load demo project: ' + err.message, 'error');
    }
  }, [onUploadSuccess, showToast, setDemoContent]);
```
> `onUploadSuccess` here is App's wrapper around `useGraphData.handleUploadSuccess`; pass
> `'demo'` as the third arg (Task 3). If App's `onUploadSuccess` does not currently forward a
> third arg, update it to forward `source`.

5. Pass `getBakedExplanation` into the `useNodeInteraction({ ... })` call:
```js
      getBakedExplanation,
```

6. Pass demo props into `<ChatDrawer ... />`:
```jsx
        isDemo={isDemo}
        getCannedChats={getCannedChats}
```

In `ProjectUpload.jsx`:

7. Real uploads must clear demo mode. `ProjectUpload` receives `onUploadSuccess`; add an
   `onClearDemo` prop and call it at the start of a successful **real** upload (not the demo
   button). App passes `onClearDemo={clearDemoContent}`. In the real upload success path
   (where `onUploadSuccess(data)` is called for an uploaded project), add `onClearDemo?.();`
   immediately before it.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd explorer && npx vitest run src/App.test.jsx`
Expected: PASS (existing + new).

- [ ] **Step 5: Commit**

```bash
git add explorer/src/App.jsx explorer/src/components/ProjectUpload.jsx explorer/src/App.test.jsx
git commit -m "feat(demo): wire pre-baked content into demo load + clear on real upload

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: Coverage/schema validation test (write before authoring content)

This test fails until Task 8 authors the full artifact — that is intended (red → green).

**Files:**
- Create: `explorer/src/utils/demoAiContent.validation.test.js`

- [ ] **Step 1: Write the test**

```js
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/utils/demoAiContent.validation.test.js`
Expected: FAIL — `Cannot find module '../../public/demo_ai_content.json'` (artifact not authored yet) or coverage gaps.

> Do not commit yet — Task 8 makes it pass, then commit both together.

---

## Task 8: Author `demo_ai_content.json` (content deliverable — by Claude)

Author the artifact so the validation test (Task 7) passes. **No API calls, no key.**

**Files:**
- Create: `explorer/public/demo_ai_content.json`

- [ ] **Step 1: Gather source + node list**

```bash
cat explorer/public/demo_graph_data.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['nodes'])); [print(n['id'], '|', n['data'].get('file')) for n in d['nodes']]"
ls app/demo_project/
```
Expected: ~41 node ids with their files (`app/demo_project/{analytics,planner,api}.py`).

- [ ] **Step 2: Read the live markdown section structure to mirror**

Read `teacher/contract.py` (`CHAT_SECTION_ORDER`, `normalize_explain_payload`,
`render_contract_text`) so each baked `technical` field uses the **same section headers + a
References section + an Unknowns section** the live endpoint renders. Read each
`app/demo_project/*.py` to author grounded, accurate content.

- [ ] **Step 3: Author the artifact**

For **every** demo node, write `snippet` (the node's real source lines) and all 3 `levels`
(`analogy`, `technical`, `key_takeaway`). Depth scales with node importance (entry-points /
public API richer; trivial helpers concise) — but every node × level is present and non-empty.
Write ~5–8 `chat` Q&A attached to a few interesting nodes (entry points / hubs), each answer in
the live References/Unknowns style. Follow the schema in the File Structure section above.

- [ ] **Step 4: Run the validation test to verify it passes**

Run: `cd explorer && npx vitest run src/utils/demoAiContent.validation.test.js`
Expected: PASS (both cases).

- [ ] **Step 5: Commit (artifact + validation test together)**

```bash
git add explorer/public/demo_ai_content.json explorer/src/utils/demoAiContent.validation.test.js
git commit -m "feat(demo): hand-authored pre-baked AI content for the demo graph

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9: Reload rehydrate (restore demo AI after a page reload)

A restored graph cached with `source:'demo'` (Task 3) should re-load the baked AI content so the
demo keeps working after a hard reload.

**Files:**
- Modify: `explorer/src/App.jsx`
- Test: `explorer/src/App.test.jsx` (add a case)

- [ ] **Step 1: Write the failing test**

```jsx
// explorer/src/App.test.jsx  (add this case)
it('rehydrates baked AI content on load when the restored graph source is demo', async () => {
  // Seed a restored demo graph in the cache before render.
  // (Use the same cacheKey/schema the app reads; see useGraphData GRAPH_CACHE_SCHEMA_VERSION.)
  // Then assert loadDemoAiContent is called on mount without clicking the demo CTA.
  loadDemoAiContent.mockResolvedValue({ explanations: {}, chat: [] });
  // ...seed localStorage cache with source:'demo' and one node...
  render(<App />);
  await waitFor(() => expect(loadDemoAiContent).toHaveBeenCalled());
});
```

> Fill the cache-seeding lines from the real `cacheKey` + `GRAPH_CACHE_SCHEMA_VERSION` values
> read in Task 3. Keep the assertion: `loadDemoAiContent` is called on mount when source is demo.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd explorer && npx vitest run src/App.test.jsx -t "rehydrates"`
Expected: FAIL — not called on mount.

- [ ] **Step 3: Write minimal implementation**

In `AppInner`, add an effect that runs once after the graph is restored: if `useGraphData`
reports the restored `source === 'demo'` (expose it from the hook), call `loadDemoAiContent()`
and `setDemoContent(ai)`:

```js
  useEffect(() => {
    if (restoredSource === 'demo') {
      loadDemoAiContent().then((ai) => setDemoContent(ai));
    }
    // run once on mount / when restoredSource resolves
  }, [restoredSource, setDemoContent]);
```

> Expose `restoredSource` (the `source` read from the cached graph) from `useGraphData` if not
> already returned.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd explorer && npx vitest run src/App.test.jsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add explorer/src/App.jsx explorer/src/hooks/useGraphData.js explorer/src/App.test.jsx
git commit -m "feat(demo): rehydrate pre-baked AI content after reload

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10: Full verification + PR + close #477

- [ ] **Step 1: Run the full frontend suite + lint + build**

```bash
cd explorer && npx vitest run && npx eslint src && npx vite build
```
Expected: all tests pass, ESLint clean, build OK.

- [ ] **Step 2: Run the repo's backend CI checks are untouched (sanity)**

No backend files changed — confirm:
```bash
git diff --name-only origin/main | grep -E '^(app|teacher|main\.py)/' || echo "no backend changes — good"
```
Expected: `no backend changes — good`.

- [ ] **Step 3: Browser smoke test**

Start the app, click the empty-state "See a live demo" CTA. Verify:
- Clicking a node shows a real AI explanation with **no API key set** and no `/api/explain`
  network call (check Network tab).
- Toggling Technical/Analogy and Beginner/Intermediate/Advanced shows baked variants.
- Chat shows suggestion chips on a node that has them; clicking replays the baked answer; a
  free-form question shows the demo wall.
- Then upload a real project (or paste a key) and confirm normal BYOK AI still works.

- [ ] **Step 4: Push + open PR**

```bash
git push -u origin feat/static-demo-ai-content-impl
gh pr create --base main --title "feat(demo): static pre-baked AI content (zero-key demo explanations + canned chat)" --body "<summary + link to spec + acceptance criteria>"
```

- [ ] **Step 5: Close #477 as superseded**

```bash
gh pr comment 477 --body "Superseded for the demo path by the static pre-baked demo AI content (PR <this-PR#>, spec: docs/superpowers/specs/2026-06-25-static-demo-ai-content-design.md), which delivers the demo 'wow' with zero key and zero server cost. Own-repo activation remains BYOK. Closing; branch kept for history."
gh pr close 477
```

> Do NOT merge this PR — leave merge for the owner's explicit approval (project rule).

---

## Self-Review (completed during planning)

- **Spec coverage:** artifact (Task 8) ✓; authoring no-API (Task 8) ✓; demo signal /
  `DemoContentContext` (Task 1) ✓; `loadDemoGraph` extension (Task 2) ✓; explanation
  interception (Task 4) ✓; chat canned + wall (Task 5) ✓; wiring + clear-on-upload (Task 6) ✓;
  error handling — `loadDemoAiContent` returns null on failure, demo graph still loads (Task 2)
  ✓; reload (Task 9) ✓; validation test (Task 7) ✓; verification + #477 close (Task 10) ✓.
  The spec's `source:'demo'` is realized via Task 3 (cache tag) + Task 9 (rehydrate); the demo
  discriminator for interception is the `DemoContentContext` presence (`isDemo`).
- **Placeholder scan:** Tasks 9's test seeding and the PR body are intentionally parameterized
  (real `cacheKey`/`PR#` values are produced during execution), not hidden logic — every code
  step shows concrete code.
- **Type consistency:** accessor names are stable across tasks — `getBakedExplanation(nodeId,
  level)`, `getCannedChats(nodeId)`, `setDemoContent(content)`, `clearDemoContent()`, `isDemo`;
  baked explanation shape `{node_id, explanation, snippet}` matches `ExplainResponse` and is used
  identically in Tasks 1, 4, 6, 8.

---

## Execution notes

- TDD throughout: red → green → commit per task.
- Frontend only. Boundaries (must not change): backend routes/prompts/models/temperature,
  `.env`, deploy config, dependencies/lockfile. Learning Path + Ghost untouched.
- Do not merge the PR or push to `main` without the owner's explicit approval.
