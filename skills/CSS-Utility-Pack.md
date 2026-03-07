# CSS Utility Pack
Use for this: Apply consistent layout, spacing, and typography utilities across the app.

Constraints: Defaults to Tailwind CSS v4. Only add custom CSS utilities when Tailwind cannot cover the pattern.
Agent note: Never duplicate what Tailwind already provides. Custom utilities use the `u-` prefix to avoid conflicts.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## When to Use Custom Utilities vs Tailwind

| Situation | Use |
|---|---|
| Standard spacing / color / flex | Tailwind directly |
| Repeated multi-class combos (3+ classes used together) | `@apply` in a utility class |
| Scrollable containers with specific behavior | Custom CSS class |
| Complex animation or pseudo-element patterns | Custom CSS class |
| One-off edge case | Inline Tailwind, no utility needed |

## Core Layout Utilities

```css
/* _utilities.css — import in globals.css */
@layer utilities {
  /* Flex shortcuts */
  .u-flex-center  { @apply flex items-center justify-center; }
  .u-flex-between { @apply flex items-center justify-between; }
  .u-flex-col     { @apply flex flex-col; }
  .u-flex-col-center { @apply flex flex-col items-center justify-center; }

  /* Grid shortcuts */
  .u-grid-auto    { @apply grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))]; }

  /* Scroll */
  .u-scroll-y     { @apply overflow-y-auto overscroll-contain scrollbar-thin; }
  .u-scroll-x     { @apply overflow-x-auto overscroll-contain scrollbar-thin; }
  .u-no-scroll    { @apply overflow-hidden; }

  /* Sizing */
  .u-full         { @apply w-full h-full; }
  .u-screen       { @apply w-screen h-screen; }
  .u-content      { @apply max-w-7xl mx-auto px-4 md:px-8; }

  /* Text */
  .u-truncate-2   { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .u-truncate-3   { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .u-text-balance { text-wrap: balance; }

  /* Visibility */
  .u-sr-only      { @apply sr-only; }  /* screen reader only */
  .u-not-sr-only  { @apply not-sr-only; }

  /* Interaction */
  .u-no-select    { @apply select-none; }
  .u-pointer      { @apply cursor-pointer; }
  .u-no-pointer   { @apply pointer-events-none; }

  /* Glass / Overlay */
  .u-glass        { @apply bg-white/5 backdrop-blur-sm border border-white/10; }
  .u-overlay      { @apply fixed inset-0 bg-black/60 backdrop-blur-sm z-50; }

  /* Focus ring */
  .u-focus-ring   { @apply focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2; }
}
```

## Usage in Components

```tsx
// Good — readable, consistent
<div className="u-flex-center gap-4">...</div>
<section className="u-content py-16">...</section>
<p className="u-truncate-2 text-sm text-muted-foreground">...</p>

// Don't create utilities for one-off spacing
// Just use Tailwind: className="mt-6 px-4"
```

## Tailwind v4 Custom Properties

```css
/* Extend in CSS, not tailwind.config */
@theme {
  --color-brand:    #9B7FE8;
  --color-surface:  #0F0F17;
  --spacing-18:     4.5rem;
  --radius-card:    0.75rem;
}
/* Then use: bg-brand, bg-surface, p-18, rounded-card */
```

## Scoping Rules
- All custom utilities use `u-` prefix
- All component-specific styles use the component's CSS module or `cn()` merging
- Never use `!important` — if needed, fix specificity instead
- All utilities go in `src/styles/_utilities.css`, imported via `globals.css`
