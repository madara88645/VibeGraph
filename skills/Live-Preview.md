# Local Preview Setup
Use for this: Run a local dev server, Storybook, or shareable preview link for testing and demos.

Constraints: Never expose secret environment variables in share URLs. Always confirm the correct port before sharing.
Agent note: Use the stack-specific commands below. Prefer Storybook for isolated component review.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Start Commands by Stack

```bash
# Next.js 15
npm run dev                     # http://localhost:3000
npm run dev -- --port 3001      # custom port

# Vite (React)
npm run dev                     # http://localhost:5173

# Storybook (component preview)
npm run storybook               # http://localhost:6006
npx storybook@latest init       # first-time setup

# Turbo monorepo
npx turbo dev --filter=web      # run specific workspace
```

## Environment Variables

```bash
# Never commit .env — use .env.local for local-only secrets
# Next.js: only vars prefixed with NEXT_PUBLIC_ are client-accessible
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# For previews, use a .env.preview file (not public)
```

## Network Sharing (Mobile / Team Testing)

```bash
# Next.js — listen on all interfaces
npm run dev -- --hostname 0.0.0.0
# Access on LAN: http://[your-ip]:3000

# Vite — automatic LAN URL shown on start
# Shows: ➜  Network: http://192.168.x.x:5173

# Public tunnel (for external sharing)
npx localtunnel --port 3000     # gives temporary public URL
# OR
npx cloudflared tunnel --url http://localhost:3000
```

## Storybook — Isolated Component Preview

```bash
# Run a story for a single component
npm run storybook -- --ci  # headless for CI

# Build static Storybook for sharing
npm run build-storybook
npx serve storybook-static  # serve built output
```

## Common Issues

| Problem | Fix |
|---|---|
| Port already in use | `npx kill-port 3000` or use `--port 3001` |
| HMR not reflecting changes | Hard refresh (Ctrl+Shift+R) or restart server |
| Env variable not found | Check prefix (`NEXT_PUBLIC_`) and restart server |
| Mobile can't connect | Use `--hostname 0.0.0.0`, check firewall rules |
| Storybook crashes on import | Add missing peer dep or mock the module in `.storybook/preview.ts` |

## Preview Checklist
```
[ ] Dev server starts without errors
[ ] Hot reload works (change a file, see update)
[ ] .env.local is loaded (check a NEXT_PUBLIC_ var in UI)
[ ] No secrets in share URL
[ ] Mobile layout tested at 375px viewport
```
