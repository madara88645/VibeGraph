# VibeGraph Header Export Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the confusing top-right PNG/SVG controls with one clear `Export` action, then tighten the header so the explorer stays readable on mobile and narrow browser widths.

**Architecture:** Keep export behavior local to `GraphViewer` so we do not widen app state. Reuse the existing export utilities and toast flow, but wrap them in a compact menu UI that behaves like the rest of the header shell. Update CSS in-place to preserve the current visual language while making the header wrap more safely on smaller screens.

**Tech Stack:** React 19, Vite, Vitest, Testing Library, CSS

---

### Task 1: Lock The Export UX With Failing Tests

**Files:**
- Modify: `explorer/src/components/GraphViewer.test.jsx`

- [ ] **Step 1: Write the failing tests for the new export entry point**

Add tests that expect a visible `Export` trigger, reveal `Export as PNG` and `Export as SVG` after click, and close the menu after selection.

```jsx
it('renders a single export trigger', () => {
  renderViewer();
  expect(screen.getByRole('button', { name: 'Export' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Export as PNG' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Export as SVG' })).not.toBeInTheDocument();
});

it('reveals PNG and SVG actions when export is opened', async () => {
  const user = userEvent.setup();
  renderViewer();

  await user.click(screen.getByRole('button', { name: 'Export' }));

  expect(screen.getByRole('button', { name: 'Export as PNG' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Export as SVG' })).toBeInTheDocument();
});

it('closes the export menu after choosing PNG', async () => {
  const user = userEvent.setup();
  renderViewer();

  await user.click(screen.getByRole('button', { name: 'Export' }));
  await user.click(screen.getByRole('button', { name: 'Export as PNG' }));

  await waitFor(() => {
    expect(mockExportAsPng).toHaveBeenCalled();
  });
  expect(screen.queryByRole('button', { name: 'Export as PNG' })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run the focused test file and verify it fails for the expected reason**

Run: `npx vitest run src/components/GraphViewer.test.jsx`

Expected: FAIL because the current UI still renders separate `PNG` and `SVG` buttons instead of one `Export` trigger.

- [ ] **Step 3: Keep or adapt the existing export success/error tests**

Rewrite the current PNG/SVG action tests so they first open the export menu, then click the action.

```jsx
await user.click(screen.getByRole('button', { name: 'Export' }));
await user.click(screen.getByRole('button', { name: 'Export as SVG' }));
```

- [ ] **Step 4: Re-run the focused test file and confirm it still fails only on missing behavior**

Run: `npx vitest run src/components/GraphViewer.test.jsx`

Expected: FAIL only because production code has not been updated yet.

- [ ] **Step 5: Commit checkpoint**

```bash
git add explorer/src/components/GraphViewer.test.jsx
git commit -m "test: cover compact export menu behavior"
```

### Task 2: Implement The Compact Export Menu

**Files:**
- Modify: `explorer/src/components/GraphViewer.jsx`

- [ ] **Step 1: Add the minimal local state for the export menu**

```jsx
const [exportMenuOpen, setExportMenuOpen] = useState(false);
```

- [ ] **Step 2: Add one export trigger and render the action menu only when open**

Use a small button labelled `Export` plus a compact popover that contains the two existing actions.

```jsx
<div className="export-controls">
  <button
    type="button"
    className="export-trigger"
    aria-haspopup="menu"
    aria-expanded={exportMenuOpen}
    aria-label={isExporting ? 'Export in progress...' : 'Export'}
    onClick={() => setExportMenuOpen((prev) => !prev)}
    disabled={isExporting}
  >
    <span>Export</span>
  </button>

  {exportMenuOpen ? (
    <div className="export-menu" role="menu" aria-label="Export options">
      <button type="button" className="export-menu-item" role="menuitem" onClick={handleExportPng}>
        Export as PNG
      </button>
      <button type="button" className="export-menu-item" role="menuitem" onClick={handleExportSvg}>
        Export as SVG
      </button>
    </div>
  ) : null}
</div>
```

- [ ] **Step 3: Close the menu when an export action succeeds or fails**

Keep the behavior simple and predictable.

```jsx
const closeExportMenu = () => setExportMenuOpen(false);

const handleExportPng = async () => {
  setIsExporting(true);
  try {
    await exportAsPng(graphRef.current);
    showToast('Graph exported as PNG', 'success');
  } catch {
    showToast('PNG export failed', 'error');
  } finally {
    closeExportMenu();
    setIsExporting(false);
  }
};
```

- [ ] **Step 4: Run the focused export tests and verify they pass**

Run: `npx vitest run src/components/GraphViewer.test.jsx`

Expected: PASS

- [ ] **Step 5: Commit checkpoint**

```bash
git add explorer/src/components/GraphViewer.jsx explorer/src/components/GraphViewer.test.jsx
git commit -m "feat: replace export buttons with compact menu"
```

### Task 3: Make The Header Behave Better On Narrow Screens

**Files:**
- Modify: `explorer/src/index.css`
- Verify: `explorer/src/App.jsx`

- [ ] **Step 1: Restyle the export trigger to match the header action language**

Add focused styles for the trigger and menu, instead of reusing the old floating button look.

```css
.export-controls {
  position: absolute;
  top: 18px;
  right: 18px;
}

.export-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.export-menu {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
}
```

- [ ] **Step 2: Improve narrow-width behavior**

Make the header wrap more intentionally and keep the export menu inside the viewport.

```css
@media (max-width: 768px) {
  .vibe-header {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .export-controls {
    top: 12px;
    right: 12px;
  }

  .export-menu {
    right: 0;
    width: min(220px, calc(100vw - 24px));
  }
}
```

- [ ] **Step 3: Make sure the header still keeps the product name, model badge, search, and upload readable**

Adjust only what is needed in the existing CSS blocks. Do not rewrite the whole shell.

- [ ] **Step 4: Run app-level tests and lint/build checks**

Run:
- `npx vitest run src/App.test.jsx src/components/GraphViewer.test.jsx`
- `npm run lint`
- `npm run build`

Expected:
- Tests PASS
- Lint PASS
- Build PASS

- [ ] **Step 5: Commit checkpoint**

```bash
git add explorer/src/index.css explorer/src/App.jsx explorer/src/components/GraphViewer.jsx explorer/src/components/GraphViewer.test.jsx
git commit -m "style: improve header export layout on mobile"
```

### Task 4: Verify In The Browser

**Files:**
- Verify only: `explorer/src/components/GraphViewer.jsx`
- Verify only: `explorer/src/index.css`

- [ ] **Step 1: Load the local app and verify desktop behavior**

Check:
- `Export` is visible in the top-right
- `PNG` and `SVG` are not permanently shown
- Clicking `Export` reveals both actions

- [ ] **Step 2: Switch to a narrow viewport and verify mobile behavior**

Check:
- Header items do not collide
- Search stays usable
- Export menu remains on-screen

- [ ] **Step 3: Record any final CSS adjustment if the browser check reveals a real issue**

Only make a small follow-up tweak if needed.

- [ ] **Step 4: Re-run the affected frontend tests after any browser-driven tweak**

Run: `npx vitest run src/components/GraphViewer.test.jsx src/App.test.jsx`

Expected: PASS

- [ ] **Step 5: Final verification**

Run:
- `npx vitest run`
- `npm run lint`
- `npm run build`

Expected:
- PASS
