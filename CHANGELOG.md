# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-05-07

### Added
- Multi-language analyzer architecture: JavaScript (.js, .jsx, .mjs, .cjs) and TypeScript (.ts, .tsx) support via tree-sitter
- analyst/languages/ plugin system with LanguageAnalyzer Protocol (analyst/languages/base.py)
- GET /api/languages endpoint returning supported language list with extensions
- Per-language node stamping (data.language field on every graph node)
- TypeScript-aware import filtering: import type statements excluded from runtime edges
- NestJS/Angular route decorator detection (@Get, @Post, @Controller) marking api_boundary=True
- First-steps onboarding banner updated to mention JS/TS project uploads

### Changed
- Upload validation now accepts Python, JS, and TS files (previously Python-only)
- Error messages updated to reference all supported languages

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
