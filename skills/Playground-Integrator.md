# Embed Playground & Share
Use for this: Create shareable interactive demos using StackBlitz, CodeSandbox, or local iframe embeds.

Constraints: Never include real API keys, database credentials, or auth tokens in playgrounds. Use mock data only.
Agent note: Prefer StackBlitz for Next.js, CodeSandbox for React/Vite. Always test iframe embeds locally before sharing.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Platform Quick Reference

| Platform | Best For | Setup |
|---|---|---|
| **StackBlitz** | Next.js, fullstack | `npx @stackblitz/sdk` or web UI |
| **CodeSandbox** | React, Vite, static | Web UI import from GitHub |
| **Storybook** | Isolated components | `npm run storybook` |
| **Local iframe** | Internal demos only | `<iframe src="http://localhost:3000">` |

## StackBlitz — Share a Next.js Demo

```bash
# Option 1: Open from GitHub repo
https://stackblitz.com/github/[user]/[repo]

# Option 2: Create programmatically (in Node script)
import sdk from '@stackblitz/sdk'
sdk.openProject({
  title: 'My Demo',
  template: 'node',
  files: {
    'package.json': JSON.stringify({ ... }),
    'app/page.tsx': `export default function Page() { return <h1>Hello</h1> }`,
  },
})
```

## CodeSandbox — Share a React Demo

```bash
# Fastest: paste a GitHub URL
https://codesandbox.io/p/github/[user]/[repo]

# Or use the API to create a sandbox
curl https://codesandbox.io/api/v1/sandboxes/define \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{ "files": { "App.tsx": { "content": "..." } } }'
```

## Local iframe Embed

```html
<!-- Use only for internal/local demos, never public sites -->
<iframe
  src="http://localhost:3000/demo"
  width="100%"
  height="600"
  style="border: none; border-radius: 8px;"
  title="Component Demo"
  sandbox="allow-scripts allow-same-origin"
/>
```

## Safe Demo Data Pattern

```ts
// mock-data.ts — use instead of real API calls in playground
export const MOCK_USERS = [
  { id: '1', name: 'Jane Doe', email: 'jane@example.com', role: 'admin' },
  { id: '2', name: 'John Smith', email: 'john@example.com', role: 'user' },
]

// In playground: import { MOCK_USERS } from './mock-data'
// Never connect to real DB, real auth, or expose .env vars
```

## Security Rules for Playgrounds
- No real API keys — use `NEXT_PUBLIC_KEY=demo` or mocked handlers
- No user PII — use faker-generated data
- Use `sandbox="allow-scripts"` on iframes to restrict behavior
- Disable network requests in demos using MSW (Mock Service Worker)

```ts
// MSW handler for playground (no real network calls)
import { http, HttpResponse } from 'msw'
export const handlers = [
  http.get('/api/users', () => HttpResponse.json(MOCK_USERS)),
]
```

## Playground Checklist
```
[ ] No secrets or real credentials
[ ] Mock data is realistic but fake
[ ] App starts with zero config (no .env required)
[ ] iframe uses sandbox attribute
[ ] Share URL tested in incognito window
[ ] README or comment explains what's being demoed
```
