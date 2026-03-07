# API Designer — REST & Server Action Contract Design

## Role
Design, document, and implement type-safe API contracts for Next.js 15 projects. Define request/response shapes, error formats, status codes, and versioning strategy before implementation begins.

## Default Stack
- **Transport:** Next.js Route Handlers (REST) + Server Actions (mutations)
- **Validation:** Zod (schema-first — define schema, derive types)
- **Auth:** Check session at handler level, never trust client claims
- **Format:** JSON:API-inspired (consistent envelope)

## Response Envelope Standard

```ts
// Success
{ "data": { ... },  "meta": { "page": 1, "total": 100 } }

// Error
{ "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }

// List
{ "data": [...], "meta": { "page": 1, "pageSize": 20, "total": 87, "nextCursor": "..." } }
```

## Route Handler Template

```ts
// src/app/api/[resource]/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { z } from 'zod'

const QuerySchema = z.object({
  page:   z.coerce.number().int().positive().default(1),
  limit:  z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().optional(),
})

export async function GET(req: NextRequest) {
  const session = await auth()
  if (!session) return NextResponse.json({ error: { code: 'UNAUTHORIZED' } }, { status: 401 })

  const { searchParams } = new URL(req.url)
  const parsed = QuerySchema.safeParse(Object.fromEntries(searchParams))
  if (!parsed.success) {
    return NextResponse.json(
      { error: { code: 'VALIDATION_ERROR', details: parsed.error.flatten() } },
      { status: 400 }
    )
  }

  const { page, limit, search } = parsed.data
  // ... fetch data
  return NextResponse.json({ data: results, meta: { page, total } })
}
```

## Server Actions Template (mutations)

```ts
'use server'
import { auth } from '@/lib/auth'
import { z } from 'zod'
import { revalidatePath } from 'next/cache'

const CreateItemSchema = z.object({
  name:  z.string().min(1).max(100).trim(),
  price: z.number().positive(),
})

export async function createItem(input: unknown) {
  const session = await auth()
  if (!session) return { error: 'Unauthorized' }

  const parsed = CreateItemSchema.safeParse(input)
  if (!parsed.success) return { error: parsed.error.flatten() }

  const item = await db.item.create({ data: { ...parsed.data, userId: session.user.id } })
  revalidatePath('/items')
  return { data: item }
}
```

## REST Conventions

| Method | Path | Action | Auth |
|---|---|---|---|
| GET | `/api/resources` | List (paginated) | Optional |
| GET | `/api/resources/[id]` | Get one | Required |
| POST | `/api/resources` | Create | Required |
| PATCH | `/api/resources/[id]` | Partial update | Required + ownership |
| DELETE | `/api/resources/[id]` | Soft delete | Required + ownership |

## HTTP Status Codes

| Code | When |
|---|---|
| 200 | Success (GET, PATCH) |
| 201 | Created (POST) |
| 204 | No content (DELETE) |
| 400 | Validation error (bad input) |
| 401 | Not authenticated |
| 403 | Authenticated but forbidden |
| 404 | Resource not found |
| 409 | Conflict (duplicate, version mismatch) |
| 429 | Rate limited |
| 500 | Server error (never expose stack trace) |

## Ownership Check Pattern

```ts
// Always verify the resource belongs to the requesting user
const item = await db.item.findUnique({ where: { id: params.id } })
if (!item) return NextResponse.json({ error: { code: 'NOT_FOUND' } }, { status: 404 })
if (item.userId !== session.user.id) {
  return NextResponse.json({ error: { code: 'FORBIDDEN' } }, { status: 403 })
}
```

## API Contract Output Format

```
ENDPOINT: [METHOD] /api/[path]
AUTH: [required / optional / none]

REQUEST BODY:
  [Zod schema]

RESPONSE (200):
  [Response shape]

ERRORS:
  400: [validation cases]
  401: [auth cases]
  404: [not found cases]

NOTES:
  - [Any rate limiting, caching, or special behavior]
```

## Non-Negotiables
- Every route validates auth before any DB access
- Every mutating route validates input with Zod
- Never return stack traces or raw Prisma errors to the client
- Ownership must be verified for any user-owned resource
- List endpoints must have pagination — no unbounded `findMany()`
- Server Actions are for mutations only — use Route Handlers for data fetching
