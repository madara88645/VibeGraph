# VibeGraph Header And Export Layout Design

## Goal

Make the explorer shell easier to understand by turning the current export area into one small, obvious `Export` action, while also improving header clarity and mobile behavior.

## Problem

The current top-right export controls show `PNG` and `SVG` as isolated buttons. They look detached from the rest of the header, do not clearly communicate that they are export actions, and consume valuable space on smaller screens. On narrow widths, the header already competes with search, upload, model badges, and utility actions, so the export controls become part of the layout pressure.

## Product Outcome

- Users should immediately understand where export lives.
- The header should feel like one intentional shell instead of several unrelated floating controls.
- On mobile and narrow browser widths, the top area should stay usable without visual collisions or ambiguous actions.

## Scope

This change only covers the frontend explorer shell and export presentation.

Included:
- Header information hierarchy
- Export control redesign
- Responsive behavior for narrow widths
- Tests for export visibility and compact layout behavior

Not included:
- New export formats
- Backend or API changes
- Reworking the graph canvas itself
- Persisting header layout preferences

## Design Direction

### 1. Header hierarchy

The header should read as three zones:

- Left: logo and product name
- Middle: passive status information like model and current file
- Right: interactive actions like AI settings, learn, theme, upload, search, and export

The goal is to reduce the feeling that every item has the same importance.

### 2. Export becomes one entry point

Replace the always-visible `PNG` and `SVG` buttons with one compact `Export` button in the top-right action cluster.

Behavior:
- Default closed
- Click opens a small menu or popover
- Menu contains `Export PNG` and `Export SVG`
- While an export is running, the button shows a busy state and export actions are temporarily disabled

This keeps the feature visible while removing unnecessary constant noise.

### 3. Mobile behavior

On narrow screens:
- The header may wrap into controlled rows instead of forcing everything into one line
- Search should remain usable and readable
- The export trigger stays visible as a single button
- The export menu should open inside the viewport and not overflow off-screen

The export interaction should not rely on hover. It must work comfortably with tap.

## Component Changes

### `explorer/src/components/GraphViewer.jsx`

- Move from two inline export buttons to one export trigger
- Add local open/close state for the export menu
- Preserve existing export logic for PNG and SVG
- Preserve success and error toast behavior
- Close the menu after a successful selection

### `explorer/src/index.css`

- Restyle the export control to look like a compact header action
- Add a dropdown or popover surface for export options
- Make the header action area wrap more gracefully on smaller widths
- Ensure the export menu aligns safely on desktop and mobile

### `explorer/src/App.jsx`

- Keep the existing shell structure
- If needed, make only small class or ordering adjustments so the export trigger feels like part of the same header system
- No API shape changes

## Data And State Flow

- Export format selection stays inside `GraphViewer`
- Existing `isExporting` state remains the source of truth for loading/disabled behavior
- New UI-only state tracks whether the export menu is open

No backend state or global app state is needed.

## Accessibility

- The export trigger should have a clear accessible name: `Export`
- The menu items should expose clear names: `Export as PNG`, `Export as SVG`
- The trigger should expose expanded/collapsed state
- Keyboard access should continue to work for opening the menu and choosing an action
- Mobile/touch interaction must not depend on tiny hit areas

## Error Handling

Existing export error handling stays unchanged:
- Failed PNG export shows the same error toast
- Failed SVG export shows the same error toast

New UI behavior:
- If export is already running, duplicate actions should be blocked
- If the menu is open during export start, keep the UI stable and prevent duplicate clicks

## Testing Strategy

### Unit and component tests

- `GraphViewer` should render a visible `Export` trigger
- Opening the trigger should reveal `Export as PNG` and `Export as SVG`
- Choosing each item should call the existing export utilities
- The menu should close after a selection
- Loading state should disable repeat export actions

### Layout and integration tests

- `App` or relevant integration tests should confirm the compact header still renders with `Visualize your codebase`
- Narrow-width responsive behavior should be checked through browser verification

## Risks

Low risk.

Main risks:
- Header wrapping may create spacing regressions on unusual viewport widths
- Menu positioning may need a small adjustment if it conflicts with other floating UI

These risks are contained to the frontend shell and should be caught by component tests plus live browser verification.

## Recommendation

Use one compact `Export` trigger with a small action menu.

Rationale:
- Most understandable for users
- Best space efficiency
- Cleanest path for mobile compatibility
