# UI Theme Generator
Use for this: Generate a complete, production-ready theme token system for a new or existing UI.

Constraints: Output tokens as CSS variables + Tailwind config + JSON. Provide light and dark variants.
Agent note: Only suggest open-source fonts. Validate contrast ratios before outputting.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## How to Use
Tell the agent:
- **Aesthetic:** (e.g., dark luxury, clean minimal, vibrant startup, corporate professional)
- **Accent color:** (or let it choose)
- **Framework:** (Tailwind / plain CSS / CSS-in-JS)
- **Dark mode?** (default dark / default light / both)

## Default Dark Luxury Theme

### CSS Variables
```css
:root {
  /* Backgrounds */
  --bg-base:     #0A0A0D;
  --bg-surface:  #141418;
  --bg-elevated: #1C1C22;
  --bg-overlay:  rgba(0,0,0,0.6);

  /* Text */
  --text-primary:   #EEEEF5;
  --text-secondary: #8A8AA8;
  --text-muted:     #5A5A78;
  --text-on-accent: #FFFFFF;

  /* Borders */
  --border-subtle: #242430;
  --border-strong: #34344A;

  /* Accent (Ice Purple) */
  --accent:         #9B7FE8;
  --accent-hover:   #8B6CD8;
  --accent-subtle:  rgba(155,127,232,0.12);
  --accent-glow:    rgba(155,127,232,0.25);

  /* Semantic */
  --success:     #4DB885;
  --success-bg:  rgba(77,184,133,0.12);
  --warning:     #F5A524;
  --warning-bg:  rgba(245,165,36,0.12);
  --danger:      #E8504A;
  --danger-bg:   rgba(232,80,74,0.12);
  --info:        #5BA4F5;
  --info-bg:     rgba(91,164,245,0.12);

  /* Spacing */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px;
  --space-4: 16px; --space-6: 24px; --space-8: 32px;
  --space-12: 48px; --space-16: 64px;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm:    0 2px 8px rgba(0,0,0,0.4);
  --shadow-md:    0 4px 24px rgba(0,0,0,0.5);
  --shadow-lg:    0 8px 40px rgba(0,0,0,0.6);
  --shadow-accent: 0 0 32px rgba(155,127,232,0.2);

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'Fira Code', 'JetBrains Mono', monospace;

  /* Transitions */
  --transition-fast:   80ms ease;
  --transition-normal: 150ms ease;
  --transition-slow:   300ms ease;
}
```

### Tailwind Config Extension
```ts
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          base:     'var(--bg-base)',
          surface:  'var(--bg-surface)',
          elevated: 'var(--bg-elevated)',
        },
        text: {
          primary:   'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted:     'var(--text-muted)',
        },
        border: {
          subtle: 'var(--border-subtle)',
          strong: 'var(--border-strong)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          hover:   'var(--accent-hover)',
          subtle:  'var(--accent-subtle)',
        },
        success: 'var(--success)',
        warning: 'var(--warning)',
        danger:  'var(--danger)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      boxShadow: {
        soft:   'var(--shadow-md)',
        accent: 'var(--shadow-accent)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'monospace'],
      },
    },
  },
} satisfies Config
```

### tokens.json (design tool export)
```json
{
  "color": {
    "bg-base":     { "value": "#0A0A0D" },
    "bg-surface":  { "value": "#141418" },
    "text-primary":{ "value": "#EEEEF5" },
    "accent":      { "value": "#9B7FE8" },
    "danger":      { "value": "#E8504A" },
    "success":     { "value": "#4DB885" }
  },
  "radius": {
    "sm": { "value": "6px" },
    "md": { "value": "10px" },
    "lg": { "value": "16px" }
  }
}
```

## Light Theme Variant
```css
.light {
  --bg-base:      #FAFAFA;
  --bg-surface:   #FFFFFF;
  --bg-elevated:  #F0F0F5;
  --text-primary: #0A0A0D;
  --text-secondary:#5A5A78;
  --border-subtle: #E4E4F0;
  --border-strong: #C8C8E0;
  --accent:        #7B5FD0;
}
```
