# Accessibility Quick Check
Use for this: Comprehensive accessibility audit and copy-paste fixes before release or review.

Constraints: Focus on actionable, copy-paste-ready fixes. Prioritize by user impact.
Agent note: Verify technical accuracy, never suggest removing existing accessibility features.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Quick Audit Checklist

### 1. Color Contrast
```bash
# Test with browser DevTools: Elements > Accessibility > Computed > Contrast Ratio
# Required: 4.5:1 for body text, 3:1 for large text (18px+ bold, 24px+ normal), 3:1 for UI components
```
**Common Fixes:**
```css
/* FAIL: Low contrast placeholder */
::placeholder { color: #aaa; }  /* 2.5:1 on white */
/* FIX */
::placeholder { color: #767676; }  /* 4.6:1 on white */

/* FAIL: Light gray on white */
.label { color: #bbb; }
/* FIX */
.label { color: #595959; }  /* 7:1 on white */
```

### 2. Keyboard Navigation
Every interactive element must be reachable and operable by keyboard only.
```tsx
// FAIL: div used as button
<div onClick={handleClick}>Click me</div>

// FIX: Use button with keyboard support built-in
<button onClick={handleClick} type="button">Click me</button>

// FIX: If you must use div (custom components)
<div
  role="button"
  tabIndex={0}
  onClick={handleClick}
  onKeyDown={(e) => e.key === 'Enter' || e.key === ' ' ? handleClick() : null}
>
  Click me
</div>
```

### 3. Focus States
```css
/* FAIL: Hidden focus ring */
button:focus { outline: none; }

/* FIX: Custom focus ring */
button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 4px;
}
```

### 4. Form Labels
```tsx
// FAIL: Unlabeled input
<input type="email" placeholder="Enter email" />

// FIX: Explicit label
<label htmlFor="email">Email address</label>
<input id="email" type="email" placeholder="name@example.com" />

// FIX: Or aria-label for icon-only inputs
<input type="search" aria-label="Search products" />
```

### 5. Images & Icons
```tsx
// FAIL: Missing alt
<img src="hero.jpg" />

// FIX: Meaningful alt
<img src="hero.jpg" alt="Dashboard showing monthly revenue chart" />

// FIX: Decorative image
<img src="decoration.svg" alt="" aria-hidden="true" />

// FIX: Icon buttons need labels
<button aria-label="Delete item">
  <TrashIcon aria-hidden="true" />
</button>
```

### 6. ARIA Landmarks
```tsx
// Required on every page
<header>...</header>
<nav aria-label="Main navigation">...</nav>
<main id="main-content">...</main>
<footer>...</footer>

// Skip link (first element in body)
<a href="#main-content" className="sr-only focus:not-sr-only">
  Skip to main content
</a>
```

### 7. Error Messages
```tsx
// FAIL: Visual-only error
<input className="border-red-500" />
<span className="text-red-500">Required</span>

// FIX: Programmatic association
<input
  aria-invalid={hasError}
  aria-describedby={hasError ? 'email-error' : undefined}
/>
{hasError && (
  <span id="email-error" role="alert">
    Email address is required
  </span>
)}
```

### 8. Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Priority Order
1. **P0 (Block release):** Missing labels, keyboard traps, contrast < 3:1 on text
2. **P1 (Fix this sprint):** Focus states missing, unlabeled icons, form errors not announced
3. **P2 (Next sprint):** Reduce motion, skip links, landmark refinements

## Quick Tools
- Browser: DevTools > Lighthouse > Accessibility
- Extension: axe DevTools (Chrome)
- CLI: `npx axe-cli http://localhost:3000`
- VS Code: axe Accessibility Linter extension
