# API Contracts (Zod-First)
Use for this: Design type-safe API schemas with Zod, including request validation, response shapes, and error formats.

Constraints: Schema first — generate types from Zod, never the reverse. All inputs validated server-side.
Agent note: Never expose internal IDs or sensitive data in response schemas. Always validate on the server.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Zod-First Approach

### Why Zod-First?
1. Schema is the single source of truth
2. Types are inferred — no duplication
3. Validation runs at runtime boundary (API route)
4. Errors are structured and predictable

## Request Schema Patterns

### Create Resource
```ts
// lib/validations/project.ts
import { z } from 'zod'

export const CreateProjectSchema = z.object({
  name: z.string().min(1, 'Name required').max(100),
  description: z.string().max(500).optional(),
  visibility: z.enum(['private', 'public']).default('private'),
  tags: z.array(z.string().max(30)).max(10).default([]),
})

export type CreateProjectInput = z.infer<typeof CreateProjectSchema>
```

### Update Resource (Partial)
```ts
export const UpdateProjectSchema = CreateProjectSchema.partial().extend({
  id: z.string().cuid(),  // ID required for updates
})
```

### Query/Filter Schema
```ts
export const ListProjectsSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  search: z.string().max(100).optional(),
  sort: z.enum(['name', 'createdAt', 'updatedAt']).default('createdAt'),
  order: z.enum(['asc', 'desc']).default('desc'),
})
```

### Nested / Relational
```ts
export const CreatePostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1).max(50000),
  tags: z.array(z.string()).max(5).default([]),
  publishedAt: z.coerce.date().optional(),
})
```

## Response Schema Patterns

### Single Resource
```ts
// Define output (safe subset — no passwords, tokens)
export const ProjectSchema = z.object({
  id:          z.string().cuid(),
  name:        z.string(),
  description: z.string().nullable(),
  visibility:  z.enum(['private', 'public']),
  createdAt:   z.string().datetime(),
  updatedAt:   z.string().datetime(),
  author: z.object({
    id:   z.string().cuid(),
    name: z.string().nullable(),
  }),
})

export type Project = z.infer<typeof ProjectSchema>
```

### Paginated List
```ts
export const PaginatedProjectsSchema = z.object({
  items: z.array(ProjectSchema),
  pagination: z.object({
    total:      z.number(),
    page:       z.number(),
    limit:      z.number(),
    totalPages: z.number(),
    hasMore:    z.boolean(),
  }),
})
```

## Unified Error Format
```ts
// All API errors follow this shape
export const ApiErrorSchema = z.object({
  error: z.object({
    code:    z.string(),    // "VALIDATION_ERROR" | "NOT_FOUND" | "UNAUTHORIZED"
    message: z.string(),   // human-readable
    details: z.record(z.array(z.string())).optional(), // field-level errors
  }),
})

// Example Zod validation error response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {
      "name": ["Name is required"],
      "tags": ["Maximum 10 tags allowed"]
    }
  }
}
```

## API Route Implementation Pattern
```ts
// app/api/projects/route.ts
import { NextResponse } from 'next/server'
import { getServerSession } from 'next-auth'
import { CreateProjectSchema } from '@/lib/validations/project'
import { db } from '@/lib/db'

export async function POST(req: Request) {
  // 1. Auth check
  const session = await getServerSession()
  if (!session) return NextResponse.json(
    { error: { code: 'UNAUTHORIZED', message: 'Authentication required' } },
    { status: 401 }
  )

  // 2. Parse + validate input
  const body = await req.json().catch(() => null)
  const parsed = CreateProjectSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json(
    { error: { code: 'VALIDATION_ERROR', message: 'Invalid input',
        details: parsed.error.flatten().fieldErrors } },
    { status: 400 }
  )

  // 3. Business logic
  const project = await db.project.create({
    data: { ...parsed.data, authorId: session.user.id },
    select: { id: true, name: true, createdAt: true },
  })

  return NextResponse.json(project, { status: 201 })
}
```

## Common Zod Patterns
```ts
// URL param as CUID
z.string().cuid()

// Optional with default
z.string().optional().default('value')

// Coerce string to number (query params)
z.coerce.number().int().positive()

// Enum with type safety
z.enum(['a', 'b', 'c'] as const)

// Transform input
z.string().transform(s => s.trim().toLowerCase())

// Refine with custom validation
z.string().refine(s => isValidSlug(s), 'Invalid slug format')
```
