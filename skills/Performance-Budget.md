# Performance Budget
Use for this: Set measurable performance targets and enforce them in CI before shipping.

Constraints: Budgets are targets, not suggestions. If a change blows a budget, the fix is required before merging.
Agent note: Measure in the same environment each time (same throttling, same network). Don't compare local vs CI numbers.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Performance Targets

### Core Web Vitals (Mobile, Fast 4G throttling)
| Metric | Target | Blocker if |
|---|---|---|
| LCP | ≤ 2.5s | > 4s |
| INP | ≤ 200ms | > 500ms |
| CLS | ≤ 0.1 | > 0.25 |
| FCP | ≤ 1.8s | > 3s |
| TTFB | ≤ 800ms | > 1.5s |

### Bundle Size Limits
| Asset | Budget | Hard Limit |
|---|---|---|
| Initial JS (compressed) | ≤ 180KB | 250KB |
| Per-route chunk | ≤ 50KB | 80KB |
| Total CSS | ≤ 15KB | 25KB |
| Web fonts | ≤ 80KB total | 120KB |
| Hero images | ≤ 150KB (WebP) | 250KB |

### API Response Times (p95)
| Endpoint Type | Target | Alert |
|---|---|---|
| Static page (cached) | ≤ 50ms | > 200ms |
| List API | ≤ 300ms | > 800ms |
| Mutation API | ≤ 500ms | > 1.5s |
| Auth route | ≤ 200ms | > 500ms |

## Measuring in CI (Lighthouse CI)

```bash
# Install
npm install -g @lhci/cli

# lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000', 'http://localhost:3000/dashboard'],
      startServerCommand: 'npm run start',
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.85 }],
        'first-contentful-paint': ['error', { maxNumericValue: 1800 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['warn', { maxNumericValue: 200 }],
      },
    },
    upload: { target: 'temporary-public-storage' },
  },
}

# GitHub Actions step
- name: Lighthouse CI
  run: lhci autorun
  env:
    LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

## Bundle Budget in CI

```bash
# next-bundle-analyzer
ANALYZE=true npm run build
# Review: .next/analyze/client.html

# Bundlesize check (add to package.json)
"bundlesize": [
  { "path": ".next/static/chunks/main-*.js", "maxSize": "100 kB" },
  { "path": ".next/static/chunks/pages/**/*.js", "maxSize": "50 kB" }
]

npx bundlesize  # fails CI if over budget
```

## Measuring Core Web Vitals in App

```tsx
// src/app/layout.tsx — real user monitoring
export function WebVitals() {
  return null  // use next/dynamic in client component
}

// src/components/WebVitals.tsx
'use client'
import { useReportWebVitals } from 'next/web-vitals'

export function WebVitals() {
  useReportWebVitals((metric) => {
    // Send to analytics
    console.log(metric.name, metric.value)
    // analytics.track('web_vital', { name: metric.name, value: metric.value })
  })
  return null
}
```

## Budget Audit Template

```
PERFORMANCE BUDGET AUDIT
Page: [URL path]  |  Date: [date]  |  Branch: [branch name]
Environment: Staging  |  Network: Lighthouse Mobile throttling

CORE WEB VITALS:
  LCP:  Xs   [PASS ✓ / FAIL ✗]  Budget: 2.5s
  INP:  Xms  [PASS ✓ / FAIL ✗]  Budget: 200ms
  CLS:  X.X  [PASS ✓ / FAIL ✗]  Budget: 0.1

BUNDLE:
  Initial JS: XKB  [PASS ✓ / FAIL ✗]  Budget: 180KB
  Route chunk: XKB [PASS ✓ / FAIL ✗]  Budget: 50KB

STATUS: [ALL PASS / [N] FAILURES]

FAILURES (if any):
  [metric] — current: X, budget: Y
  Root cause: [analysis]
  Fix: [action item + owner]
```

## Quick Wins Checklist
```
[ ] Images: next/image with explicit width/height
[ ] Fonts: next/font (no external font requests)
[ ] Above-fold image: priority prop on <Image>
[ ] Heavy libs: dynamic import (charts, RTE, PDF)
[ ] Unused deps removed (check with bundlephobia)
[ ] CSS: no unused global styles
[ ] API: parallel fetching (Promise.all) where possible
[ ] DB: indexes on filtered/sorted columns
```
