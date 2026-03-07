# Error Handling Patterns
Use for this: Implement consistent error handling across Server Components, Route Handlers, Server Actions, and client UI.

Constraints: Never expose internal error details (stack traces, DB errors) to the client. Users should see actionable messages, not technical errors.
Agent note: Handle errors at the boundary closest to the user. Log full details server-side, show safe messages client-side.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Error Layers

| Layer | Catch With | Show User |
|---|---|---|
| Route Handlers | try/catch → return error response | JSON error with code |
| Server Actions | try/catch → return `{ error }` | Toast / form error |
| Server Components | `error.tsx` boundary | Friendly error page |
| Client Components | Error Boundary + `error.tsx` | Friendly recovery UI |
| Global unhandled | `app/error.tsx` | Catch-all error page |

## Route Handler Errors

```ts
// src/app/api/posts/route.ts
export async function GET(req: Request) {
  try {
    const data = await getPosts()
    return NextResponse.json({ data })
  } catch (error) {
    // Log full error server-side
    console.error('[GET /api/posts]', error)
    // Return safe message to client
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch posts' } },
      { status: 500 }
    )
  }
}
```

## Server Action Errors (return, don't throw)

```ts
'use server'
export async function createPost(input: unknown) {
  try {
    const session = await auth()
    if (!session) return { error: 'Unauthorized' }

    const parsed = CreatePostSchema.safeParse(input)
    if (!parsed.success) return { error: parsed.error.flatten() }

    const post = await db.post.create({ data: { ...parsed.data, authorId: session.user.id } })
    revalidatePath('/posts')
    return { data: post }
  } catch (error) {
    console.error('[createPost]', error)
    return { error: 'Failed to create post. Please try again.' }
  }
}
```

## error.tsx — Page-Level Error Boundary

```tsx
// src/app/error.tsx
'use client'
import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log to error tracking service (Sentry, etc.)
    console.error(error)
  }, [error])

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4 text-center">
      <h2 className="text-2xl font-semibold">Something went wrong</h2>
      <p className="text-muted-foreground max-w-md">
        We encountered an unexpected error. Our team has been notified.
      </p>
      <Button onClick={reset}>Try again</Button>
    </div>
  )
}
```

## not-found.tsx

```tsx
// src/app/not-found.tsx
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4 text-center">
      <h1 className="text-4xl font-bold">404</h1>
      <p className="text-muted-foreground">This page doesn't exist.</p>
      <Button asChild>
        <Link href="/">Go home</Link>
      </Button>
    </div>
  )
}
```

## Toast Notifications (Sonner)

```tsx
// Client component — show feedback after server action
import { toast } from 'sonner'
import { createPost } from '@/actions/posts'

async function handleSubmit(data: FormData) {
  const result = await createPost(data)
  if ('error' in result) {
    toast.error(typeof result.error === 'string' ? result.error : 'Invalid input')
  } else {
    toast.success('Post created!')
  }
}
```

## Form Validation Errors (React Hook Form + Server Action)

```tsx
const { setError, handleSubmit } = useForm<FormValues>()

async function onSubmit(values: FormValues) {
  const result = await createItem(values)
  if (result.error) {
    if (typeof result.error === 'object' && 'fieldErrors' in result.error) {
      Object.entries(result.error.fieldErrors).forEach(([field, messages]) => {
        setError(field as keyof FormValues, { message: messages?.[0] })
      })
    } else {
      toast.error(String(result.error))
    }
  }
}
```

## Client-Side Error Boundary

```tsx
'use client'
import { Component, type ReactNode } from 'react'

interface Props { children: ReactNode; fallback: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  componentDidCatch(error: Error) { console.error(error) }
  render() {
    return this.state.hasError ? this.props.fallback : this.props.children
  }
}
```

## Never Expose Internal Errors
```ts
// ❌ BAD — leaks DB details
return NextResponse.json({ error: error.message }, { status: 500 })
// PrismaClientKnownRequestError: Unique constraint failed on field 'email'

// ✅ GOOD — safe message
return NextResponse.json({ error: { code: 'CONFLICT', message: 'Email already in use' } }, { status: 409 })
```
