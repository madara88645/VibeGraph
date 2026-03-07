# Performance Measurement
Use for this: Measure, baseline, and improve UI and API performance with reproducible methods.

Constraints: State the measurement environment. Don't optimize without a baseline — measure first, then optimize.
Agent note: Avoid noisy measurements. Run benchmarks multiple times and take median, not best-case.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Core Web Vitals Targets

| Metric | Good | Needs Work | Poor |
|---|---|---|---|
| **LCP** (Largest Contentful Paint) | ≤ 2.5s | 2.5–4s | > 4s |
| **INP** (Interaction to Next Paint) | ≤ 200ms | 200–500ms | > 500ms |
| **CLS** (Cumulative Layout Shift) | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| **FCP** (First Contentful Paint) | ≤ 1.8s | 1.8–3s | > 3s |
| **TTFB** (Time to First Byte) | ≤ 800ms | 800ms–1.8s | > 1.8s |

## Measurement Tools

### Browser DevTools (Quick)
```
1. Open DevTools → Lighthouse tab
2. Check: Performance + Accessibility
3. Device: Mobile throttled (Real-world baseline)
4. Run 3× and take the median score

For runtime perf:
- DevTools → Performance → Record → Interact → Stop
- Look for: Long Tasks (> 50ms), Layout shifts, Main thread blocking
```

### CLI Measurement
```bash
# Lighthouse CI
npx lighthouse http://localhost:3000 --view

# Bundle analysis
npx @next/bundle-analyzer  # add ANALYZE=true to .env
ANALYZE=true npm run build

# With Playwright (scripted perf test)
npx playwright test perf --reporter=line
```

## Rendering Performance

### React Render Profiling
```tsx
// 1. Enable React DevTools Profiler
// 2. Record a session
// 3. Look for unexpected re-renders

// Quick re-render debug
import { useEffect, useRef } from 'react'

function useRenderCount(name: string) {
  const count = useRef(0)
  count.current++
  if (process.env.NODE_ENV === 'development') {
    console.log(`[${name}] render #${count.current}`)
  }
}
```

### Common React Performance Fixes
```tsx
// Heavy computation: memoize
const sorted = useMemo(() => items.sort(compareFn), [items])

// Stable callbacks: prevent child re-renders
const handleClick = useCallback(() => { ... }, [dep1])

// Large lists: virtualize
import { useVirtualizer } from '@tanstack/react-virtual'

// Prevent unnecessary parent re-renders
const MemoChild = memo(ChildComponent)
```

## API & DB Performance

### Query Timing
```ts
// Prisma query timing
const db = new PrismaClient({
  log: [{ emit: 'event', level: 'query' }],
})
db.$on('query', (e) => {
  if (e.duration > 100) console.warn(`Slow query (${e.duration}ms):`, e.query)
})
```

### N+1 Detection
```bash
# Check Prisma logs for repeated similar queries
# Pattern: same query running N times in a request
# Fix: add include{} or use $transaction for batching
```

### API Route Timing
```ts
// Add timing header to debug slow routes
export async function GET(req: Request) {
  const start = Date.now()
  const data = await expensiveOperation()
  const duration = Date.now() - start
  return NextResponse.json(data, {
    headers: { 'Server-Timing': `total;dur=${duration}` }
  })
}
```

## Bundle Size Targets
```
Initial JS bundle:    < 200KB (compressed)
Per-route chunk:      < 50KB
Total CSS:            < 20KB
Images:               WebP/AVIF, lazy-loaded, explicit width/height
Fonts:                ≤ 2 font families, preloaded
```

## Performance Report Template
```
MEASUREMENT DATE: [date]
ENVIRONMENT: [local / staging / production]
NETWORK: [throttling used: none / Fast 4G / Slow 4G]

BEFORE:
  LCP: Xs  |  INP: Xms  |  CLS: X.X
  Bundle: XKB  |  API p95: Xms

AFTER:
  LCP: Xs  |  INP: Xms  |  CLS: X.X
  Bundle: XKB  |  API p95: Xms

CHANGES MADE:
- [change 1] → saved Xms / XKB
- [change 2]

NEXT OPPORTUNITIES:
- [next optimization target]
```
