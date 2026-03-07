# Architecture Snapshot
Use for this: Produce a concise, actionable architecture overview for planning, onboarding, or refactoring decisions.

Constraints: Be specific, not abstract. Reference actual file paths and patterns from the codebase. Call out real risks.
Agent note: Never include credentials or production secrets. Verify assumptions against actual code.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Architecture Snapshot Template

### Overview
```
PROJECT: [name]
STACK: [e.g., Next.js 15 + TypeScript + Prisma + PostgreSQL + Tailwind]
TYPE: [Monolith / Monorepo / Microservices]
DEPLOYMENT: [Vercel / Railway / AWS / Docker]
```

### Layer Map
```
┌─────────────────────────────────────┐
│  Client (Browser)                   │
│    Next.js App Router               │
│    React components + Zustand       │
│    React Query (server state)       │
├─────────────────────────────────────┤
│  Server (Next.js)                   │
│    API Routes / Server Actions      │
│    Zod validation                   │
│    Authentication (NextAuth/Clerk)  │
├─────────────────────────────────────┤
│  Data Layer                         │
│    Prisma ORM                       │
│    PostgreSQL (Supabase/Neon)       │
│    Redis (cache/queues)             │
├─────────────────────────────────────┤
│  External Services                  │
│    Stripe (payments)                │
│    Resend (email)                   │
│    Cloudflare R2 (storage)          │
└─────────────────────────────────────┘
```

### Key Data Flows

**Flow 1: [e.g., User creates a project]**
```
Browser → POST /api/projects → Zod validation → Auth check
→ Prisma create → Return project → Invalidate React Query cache
→ Optimistic UI update
```

**Flow 2: [e.g., Auth flow]**
```
Browser → /auth/signin → NextAuth → Provider OAuth
→ JWT/Session created → Redirect → Session cookie set
```

### File Structure (key paths)
```
src/
  app/                  # Next.js App Router pages
    (auth)/             # Auth-gated routes
    api/                # API routes
  components/
    ui/                 # Design system components
    features/           # Feature-specific components
  lib/
    db.ts               # Prisma client singleton
    auth.ts             # Auth config
    validations/        # Zod schemas
  hooks/                # Custom React hooks
  stores/               # Zustand stores
prisma/
  schema.prisma         # DB schema
  migrations/           # Migration files
```

### Architectural Risks
| Risk | Severity | Notes |
|---|---|---|
| [e.g., No rate limiting on API] | High | Add Upstash rate limiting |
| [e.g., N+1 queries in dashboard] | Medium | Add `include` to Prisma queries |
| [e.g., Client bundle > 500KB] | Medium | Run `pnpm build --analyze` |
| [e.g., No DB connection pooling] | Low | Add PgBouncer or Prisma Accelerate |

### Scaling Bottlenecks (predict before they happen)
1. **DB connections** — add connection pooling before > 100 concurrent users
2. **File uploads** — move to direct-to-S3 upload before > 10MB files
3. **Server costs** — evaluate edge/serverless vs. persistent server at > 1000 req/min

### Recommended Start Points for Common Tasks
| Task | Start Here |
|---|---|
| Add new feature | `src/app/[feature]/page.tsx` → `src/lib/validations/[feature].ts` |
| Add API endpoint | `src/app/api/[resource]/route.ts` |
| Add DB table | `prisma/schema.prisma` → run `prisma migrate dev` |
| Add UI component | `src/components/ui/[Component].tsx` |
| Debug auth issue | `src/lib/auth.ts` → NextAuth config |
