# Next.js App Router Conventions
Use for this: Correct patterns, file conventions, and gotchas for Next.js 14/15 App Router.

Constraints: Server Components are the default. Only add 'use client' when you actually need it.
Agent note: Confirm Next.js version before suggesting App Router patterns. Never expose env vars without NEXT_PUBLIC_ prefix for client use.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## File & Folder Conventions

```
app/
  layout.tsx           # Root layout (always a Server Component)
  page.tsx             # Root page
  loading.tsx          # Automatic suspense boundary for the segment
  error.tsx            # Error boundary ('use client' required)
  not-found.tsx        # 404 page
  
  (auth)/              # Route group (doesn't affect URL)
    login/page.tsx
    register/page.tsx
  
  dashboard/
    layout.tsx         # Nested layout
    page.tsx
    [id]/
      page.tsx         # Dynamic route → params.id
      edit/page.tsx
  
  api/
    projects/
      route.ts         # GET, POST handlers
      [id]/
        route.ts       # GET, PUT, DELETE for /api/projects/:id
```

## Server vs. Client Components

### When to use Server Components (default)
- Fetching data
- Accessing env vars / secrets
- Heavy computation
- Static rendering
- No interactivity needed

### When to add 'use client'
- `useState` / `useReducer` / `useEffect`
- Browser APIs (`window`, `localStorage`, `navigator`)
- Event handlers (`onClick`, `onSubmit`, etc.)
- Third-party libs that use browser APIs

### Pattern: Keep 'use client' as leaf nodes
```tsx
// ✅ Good: data fetching in Server Component
// app/dashboard/page.tsx (Server Component)
async function DashboardPage() {
  const projects = await db.project.findMany()  // runs on server
  return <ProjectList projects={projects} />     // passes to client
}

// components/ProjectList.tsx
'use client'
function ProjectList({ projects }: { projects: Project[] }) {
  const [selected, setSelected] = useState<string | null>(null)
  return ...
}
```

## Data Fetching Patterns

### Server Component (recommended for initial data)
```tsx
// app/projects/page.tsx
export default async function ProjectsPage() {
  const projects = await db.project.findMany({
    where: { userId: await getCurrentUserId() },
    orderBy: { updatedAt: 'desc' },
  })
  return <ProjectList initialProjects={projects} />
}
```

### fetch with caching
```tsx
// Static (cached indefinitely)
const data = await fetch('/api/data', { cache: 'force-cache' })

// Dynamic (no cache — SSR on every request)
const data = await fetch('/api/data', { cache: 'no-store' })

// Revalidate every 60 seconds
const data = await fetch('/api/data', { next: { revalidate: 60 } })
```

### Parallel data fetching
```tsx
async function Page() {
  const [user, projects] = await Promise.all([
    getUser(),
    getProjects(),
  ])
  // ...
}
```

## Server Actions
```tsx
// app/actions/project.ts
'use server'

import { revalidatePath } from 'next/cache'
import { z } from 'zod'

const CreateSchema = z.object({ name: z.string().min(1) })

export async function createProject(formData: FormData) {
  const session = await getServerSession()
  if (!session) throw new Error('Unauthorized')
  
  const parsed = CreateSchema.safeParse({ name: formData.get('name') })
  if (!parsed.success) return { error: parsed.error.flatten() }
  
  await db.project.create({ data: { ...parsed.data, userId: session.user.id } })
  revalidatePath('/dashboard')
}

// Usage in component
<form action={createProject}>
  <input name="name" required />
  <button type="submit">Create</button>
</form>
```

## Metadata
```tsx
// Static metadata
export const metadata: Metadata = {
  title: 'Dashboard',
  description: '...',
}

// Dynamic metadata
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const project = await getProject(params.id)
  return { title: project.name }
}
```

## Middleware (for auth protection)
```ts
// middleware.ts
import { withAuth } from 'next-auth/middleware'

export default withAuth({
  callbacks: {
    authorized: ({ token }) => !!token,
  },
})

export const config = {
  matcher: ['/dashboard/:path*', '/api/projects/:path*'],
}
```

## Environment Variables
```ts
// Server-only (safe)
process.env.DATABASE_URL
process.env.NEXTAUTH_SECRET

// Client + Server (must have NEXT_PUBLIC_ prefix)
process.env.NEXT_PUBLIC_APP_URL

// Type-safe env validation (t3-env)
import { createEnv } from '@t3-oss/env-nextjs'
export const env = createEnv({
  server: { DATABASE_URL: z.string().url() },
  client: { NEXT_PUBLIC_APP_URL: z.string().url() },
  runtimeEnv: process.env,
})
```

## Common Gotchas
| Gotcha | Fix |
|---|---|
| `useSearchParams()` causes full page client render | Wrap in `<Suspense>` |
| Server Component can't use hooks | Add `'use client'` or extract to child |
| `cookies()` in Server Component returns stale data | Use `cookies()` from `next/headers` |
| `params` is now a Promise in Next.js 15 | `const { id } = await params` |
| Route groups affect layouts but not URLs | Use `(groupName)/` folders |
