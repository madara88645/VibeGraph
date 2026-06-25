# Static Pre-Baked Demo AI Content — Design

**Date:** 2026-06-25
**Author:** claude-code (brainstormed with owner)
**Status:** Approved design — ready for implementation plan
**Related:** PR #479 (landing live-demo CTA, merged), PR #477 (server-funded trial — to be closed as superseded for the demo), `monetization-readiness` memo (zero-users-first strategy)

## 1. Problem

VibeGraph's monetization/onboarding killer is the **BYO-key (BYOK) wall**: `/api/ai-config`
returns `requiresUserKey: true` and there is no server fallback key, so **no AI works until
the visitor creates an OpenRouter account and pastes a key**.

PR #479 lets a stranger load the bundled demo graph with one click (no upload, no key), but
the moment they click a node for an **AI explanation** or open **chat**, they hit the key
wall. So a cold visitor still never sees VibeGraph's core value — the AI explanations and
graph-grounded Q&A.

## 2. Goal & Non-Goals

**Goal:** When the bundled demo graph is loaded, AI **explanations** and a guided **Q&A**
work with **zero key, zero server cost, zero live LLM calls** — by serving hand-authored,
pre-baked content that is byte-compatible with the live API responses, so the UI renders it
unchanged. This is the activation "wow": a stranger feels the AI value in seconds.

**Non-goals (V1):**
- Learning Path AI refinement — already renders a deterministic baseline ordering with no
  key (`app/routers/learning.py` runs the AI refiner only when a key is present). Left as-is.
- Ghost Runner narration — already degrades to silent when no key
  (`useGhostRunner.js` early-returns if `!aiReady`). Left as-is.
- The user's **own uploaded project** — stays **BYOK**, unchanged.
- Server-funded trials, accounts, billing. (Supersedes #477 for the demo path.)

## 3. Background — current behavior (verified in code)

- **Demo load path:** `explorer/src/utils/loadDemoGraph.js` (added in #479) fetches
  `/demo_graph_data.json`, falling back to `/graph_data.json`. Used by the empty-state CTA
  (`App.jsx` `handleLoadDemo`) and the upload modal (`ProjectUpload.jsx`).
- **No demo flag exists.** Demo and uploaded data are processed identically; `useGraphData.js`
  tags the graph with a hardcoded `GRAPH_CACHE_SOURCE = 'user_upload'`. We must introduce a
  discriminator.
- **Demo data is structure-only:** `explorer/public/demo_graph_data.json` (~25 KB, 41 nodes /
  40 edges) carries no AI/explanation/source fields. The demo project source lives at
  `app/demo_project/{analytics,planner,api}.py`; live explanations extract snippets from those
  files server-side.
- **Explain response contract** (`app/routers/explain.py` → `ExplainResponse` in
  `app/models.py:299-309`):
  ```
  { "node_id": str,
    "explanation": { "analogy": str, "technical": str, "key_takeaway": str, "is_error": bool|null },
    "snippet": str }
  ```
  Important: `teacher.explain_code(...)` takes **`level`** (beginner/intermediate/advanced) but
  **not `type`**. The response always contains BOTH `analogy` and `technical`. The tab
  (technical/analogy) is a **frontend display toggle only** — so the response depends on
  `(node, level)`, not on the tab. `technical` is markdown rendered from a fixed set of grounded
  sections + a References section + an Unknowns section (`teacher/contract.py`
  `normalize_explain_payload` / `CHAT_SECTION_ORDER`).
- **Chat response contract** (`app/routers/chat.py` → `ChatResponse` in `app/models.py:322-324`):
  `{ "node_id": str|null, "answer": str }` where `answer` is a markdown string (References /
  Unknowns are inside that string). Primary endpoint is the SSE stream `/api/chat/stream`;
  `/api/chat` is the non-streaming fallback. Chat requires a selected node.
- **Frontend explanation cache** (`useNodeInteraction.js`): in-memory `Map` + localStorage
  `vg_v1_explanationCache`, keyed by `node.id__type__level__model__hashApiKey`. The pre-baked
  lookup will be inserted right after this cache check and **before** the `ensureAiReady` / key
  gate, so it serves with no key.

## 4. Design

### 4.1 Data artifact — `explorer/public/demo_ai_content.json`

A static file, **hand-authored by Claude** (see 4.2), schema-compatible with the live API:

```jsonc
{
  "version": 1,
  "generatedAt": "2026-06-25",
  "author": "claude-authored (no live API call, no key)",
  "graphFile": "demo_graph_data.json",      // which graph this content is bound to
  "explanations": {
    "<nodeId>": {                            // one entry per demo node
      "beginner":     { "analogy": "…", "technical": "…(markdown)…", "key_takeaway": "…" },
      "intermediate": { "analogy": "…", "technical": "…(markdown)…", "key_takeaway": "…" },
      "advanced":     { "analogy": "…", "technical": "…(markdown)…", "key_takeaway": "…" }
    }
    // 41 nodes × 3 levels = 123 explanation objects
  },
  "chat": [
    { "nodeId": "<id>", "question": "…", "answer": "…(markdown, References/Unknowns inside)…" }
    // a curated handful (~5–8) attached to a few key demo nodes
  ]
}
```

- Each `explanations[node][level]` object mirrors `ExplainResponse.explanation` exactly
  (`analogy`, `technical`, `key_takeaway`), so `ExplanationPanel` renders it with **no code
  change**. Keyed by `(node, level)` — the **same object serves both tabs** (tab is display-only).
- Each `chat[]` entry's `answer` is a markdown string injected as the assistant message —
  rendered by the existing chat message renderer with no change.
- `version` / `generatedAt` / `author` / `graphFile` are provenance only.

### 4.2 Authoring (no API, no key)

Claude generates the content directly — **no live OpenRouter call, no key, no cost**:

1. Read the demo project source (`app/demo_project/*.py`), the demo graph
   (`demo_graph_data.json`), and the live markdown section structure (`teacher/contract.py`
   `CHAT_SECTION_ORDER`) so the baked `technical` field **mirrors the live output's section
   layout** (the demo looks identical in style to a real run).
2. For **every** demo node, write `{analogy, technical, key_takeaway}` at all **3 levels**.
   Depth scales with node significance (entry-points / public API get richer content; trivial
   helpers stay concise) — but every node × level is present and schema-valid so **no click
   ever misses**.
3. Write ~5–8 curated Q&A pairs attached to a few interesting demo nodes (entry points /
   hubs), each answer following the live References/Unknowns style.
4. Commit `demo_ai_content.json`.

A **validation test** (`explorer/src/utils/demoAiContent.validation.test.js`, Vitest — **no
key, no network**, runs in the existing frontend test job) asserts: every node in
`demo_graph_data.json` has all 3 levels; each entry has non-empty
`analogy`/`technical`/`key_takeaway`; every `chat[].nodeId` exists in the graph. Pure file
check — no new CI runner.

### 4.3 Demo-mode signal

- Extend `loadDemoGraph()` to also fetch `demo_ai_content.json` and return both the graph and
  the baked content (AI fetch is best-effort — see 4.6).
- Introduce a demo discriminator: `useGraphData.js` tags the demo load as `source: 'demo'`
  (instead of the hardcoded `'user_upload'`), and the baked content is held in a small
  **`DemoContentContext`** (set on demo load, **cleared on any real upload**). Accessors:
  `getBakedExplanation(nodeId, level)` and `getCannedChats(nodeId)`.

### 4.4 Interception — explanations

In `useNodeInteraction.js` `fetchExplanation`, after the existing cache check and **before**
`ensureAiReady` / the `/api/explain` network call: if in demo mode and
`getBakedExplanation(node.id, level)` exists → resolve with it immediately (no key, no network).
Keyed by `(node, level)`; the same baked object is returned regardless of the `type` tab.
Otherwise fall through to today's path unchanged.

### 4.5 Interception — chat (canned Q&A)

`ChatDrawer.jsx` in demo mode:
- When a node with canned Q&As is selected, render its questions as **suggestion chips**.
- Clicking a chip appends the user message + the baked `answer` as an assistant message — **no
  network**.
- **Free-form** typing (or a question with no baked answer) → show an honest BYOK wall message
  instead of calling the API:
  > "This is a live demo with sample answers. To ask your own questions or analyze your own
  > code, add a free OpenRouter key."
- Non-demo (uploaded) chat is unchanged.

### 4.6 Error handling

- `demo_ai_content.json` missing / malformed → the demo graph still loads; AI falls back to
  today's live/walled behavior. Non-fatal; log a warning. (`loadDemoGraph` already has graph
  fallback; the AI fetch is wrapped so its failure never blocks the graph.)
- Missing baked entry for a `(node, level)` → graceful fall-through to the existing path. With
  full coverage (4.2) this should not occur; the validation script guards it.

## 5. Testing

- **Unit:** `DemoContentContext` accessors (hit/miss); `loadDemoGraph` extension (fetches both;
  swallows AI-fetch failure and still returns the graph).
- **Component — explanations:** in demo mode, selecting a node renders the baked explanation
  with **`fetch` to `/api/explain` never called** (assert not called); toggling tab and level
  serves the baked variants offline.
- **Component — chat:** demo suggestion chips render; clicking shows the baked answer with no
  network; free-form input shows the wall and makes no network call.
- **Regression:** the uploaded-project path is unchanged — explanations/chat still hit the
  network with a key; `source` is `'user_upload'`, no baked content present.
- **Validation test:** coverage (all nodes × 3 levels) + schema + chat nodeId integrity.

## 6. Scope, files, boundaries

**New:**
- `explorer/public/demo_ai_content.json` (the artifact)
- `explorer/src/utils/demoAiContent.validation.test.js` (no-key Vitest validator)
- `explorer/src/context/DemoContentContext.jsx` (+ test)

**Edited:**
- `explorer/src/utils/loadDemoGraph.js` (also fetch the AI artifact)
- `explorer/src/hooks/useGraphData.js` (`source: 'demo'` + stash baked content / clear on upload)
- `explorer/src/hooks/useNodeInteraction.js` (baked-first in `fetchExplanation`)
- `explorer/src/components/ChatDrawer.jsx` (canned chips + demo wall)
- `explorer/src/components/ProjectUpload.jsx` and `App.jsx` glue (demo load marks demo mode)

**Boundaries (must NOT change):** backend routes/prompts/models/temperature, `.env`,
deploy config, dependencies/lockfile. Learning Path and Ghost Runner are untouched. This is
frontend + one static data file + one validator script.

## 7. Acceptance criteria

1. Load the demo → clicking **any** of the 41 nodes shows an AI explanation with **no key**
   and **no network call** to `/api/explain`, at all 3 levels, for both tabs.
2. Demo chat: suggestion chips render baked answers with no network; free-form input shows the
   honest wall and makes no network call.
3. Uploading a real project is **unchanged BYOK** — explanations/chat still hit the network
   with a key.
4. Baked content renders in the **same markdown style** as live output (section layout,
   References/Unknowns).
5. Frontend test suite (incl. the validation test), ESLint, and `vite build` all green.

## 8. Relationship to #477

This statically solves the demo "wow" that #477 (server-funded trial) was meant to unlock —
at zero cost and zero abuse risk. #477 is therefore **superseded for the demo** and will be
closed with a comment linking this spec. Activation on the user's **own** repo remains BYOK
(license-key monetization, e.g. Gumroad/LemonSqueezy, if/when revenue is revisited) — no
server-key infrastructure is built now.
