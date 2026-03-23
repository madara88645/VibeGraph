# Changelog

## [2026-03-22] — UX Polish & Visual Enhancements

### Added
- **Toast Notification System** — Replaced browser `alert()` calls with non-blocking, themed toast notifications (success/error/info) with auto-dismiss and slide-in animations
- **Explanation Cache** — AI explanations are now cached per node/tab/level combination; switching between beginner→intermediate→beginner no longer re-fetches from the API
- **All Files View** — Added "All Files" button to the file sidebar to show the entire call graph at once, with easy toggle back from filtered views
- **Fullscreen Code View** — Both the bottom CodePanel and the right-side CodeViewer now have expand buttons (⛶) to open code in a fullscreen overlay via React Portal
- **Help Guide** — Added a `?` button to the simulation controls bar that opens a popover explaining Ghost Runner and Code Analyzer features
- **Visual Animations & Micro-interactions**
  - Node hover: lift + scale + accent-colored glow
  - Node selection: pulse animation + persistent glow
  - Button press feedback: scale(0.93) on all interactive buttons
  - Pause button: breathing red glow while simulation runs
  - Chat FAB: breathing blue glow idle animation
  - Chat messages: slide-in entrance animations (user from right, assistant from below)
  - Tab switching: animated underline indicator
  - Content transitions: fade-up animation on explanation changes
  - Learning path: shimmer effect on progress bar
  - Sidebar files: hover glow + selection flash
  - Search results: horizontal slide on hover/highlight
  - Header buttons: lift + shadow on hover
  - Upload zone: lift + shadow on hover

### Changed
- Chat FAB repositioned (`left: 20px` → `left: 64px`) to prevent overlap with React Flow zoom controls
- CustomNode refactored from inline styles to CSS classes (`.vg-node`) enabling proper `:hover` pseudo-class support
- `sse.test.js` migrated from `node:test` to vitest for consistency

### Testing
- Added vitest + @testing-library/react + jsdom as frontend test infrastructure
- **18 new frontend tests** covering:
  - Toast notification rendering, dismissal, auto-timeout, and error boundaries
  - SimulationControls help guide: open, close, toggle, content verification
  - Explanation cache: hit/miss behavior, cross-parameter fetch, reset invalidation
  - SSE chunk parsing (migrated to vitest)
- All **93 backend tests** continue to pass
- Frontend build (`vite build`) passes cleanly
