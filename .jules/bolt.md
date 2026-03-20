## 2024-05-24 - React Flow Unnecessary Re-renders
**Learning:** In React Flow, state arrays like `nodes` and `edges` trigger O(N) full re-renders on every tick during rapid animations (like Ghost Runner) if object references change, even when visual properties haven't.
**Action:** When mapping over `nodes` or `edges` state to update classes/styles, preserve the exact object references for items whose properties haven't changed.
## 2024-05-24 - React Heavy UI Components Re-rendering
**Learning:** In the VibeGraph React frontend, the `App` component frequently updates global `nodes` and `edges` state (e.g., during 'Ghost Runner' ticks). This causes heavy UI components like `FileSidebar`, `ExplanationPanel`, `ChatDrawer`, and `CodePanel` to re-render constantly even when their props haven't changed, leading to O(N) performance bottlenecks.
**Action:** Use `React.memo()` to wrap these heavy UI components so they only re-render when their specific props change.
