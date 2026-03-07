# TypeScript Patterns
Use for this: Apply advanced TypeScript patterns to improve type safety, code clarity, and maintainability.

Constraints: Use the simplest type that solves the problem. Don't generate complex types for the sake of complexity.
Agent note: Prefer explicit types over inference for public APIs. Trust inference for local variables.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Strict Config (always enabled)

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true
  }
}
```

## Discriminated Unions (handle state clearly)

```ts
// Instead of: { data?: T; error?: Error; loading: boolean }
type Result<T> =
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: Error }

function render(result: Result<User>) {
  switch (result.status) {
    case 'loading': return <Spinner />
    case 'error':   return <Error message={result.error.message} />
    case 'success': return <Profile user={result.data} />  // TS knows data exists here
  }
}
```

## Type Guards

```ts
// Runtime check that gives TS type narrowing
function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value &&
    typeof (value as User).email === 'string'
  )
}

// Use with external data
const parsed = await response.json()
if (!isUser(parsed)) throw new Error('Invalid user response')
// parsed is now typed as User
```

## Generics — Practical Patterns

```ts
// Generic service function
async function fetchById<T>(model: string, id: string): Promise<T | null> {
  // ...
}

// Generic with constraint
function pick<T extends object, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
  return Object.fromEntries(keys.map(k => [k, obj[k]])) as Pick<T, K>
}

// Generic React component
interface ListProps<T> {
  items: T[]
  renderItem: (item: T) => React.ReactNode
  keyExtractor: (item: T) => string
}
function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return <ul>{items.map(item => <li key={keyExtractor(item)}>{renderItem(item)}</li>)}</ul>
}
```

## Utility Types Reference

```ts
// Extract fields from a type
type UserPreview = Pick<User, 'id' | 'name' | 'avatar'>

// Remove fields
type PublicUser = Omit<User, 'passwordHash' | 'internalNotes'>

// Make all optional
type PartialConfig = Partial<Config>

// Make all required
type RequiredConfig = Required<Partial<Config>>

// Make all readonly
type FrozenUser = Readonly<User>

// Infer return type
type AsyncReturnType<T extends (...args: any) => Promise<any>> =
  T extends (...args: any) => Promise<infer R> ? R : never

// Infer Zod schema type
import { z } from 'zod'
const UserSchema = z.object({ id: z.string(), name: z.string() })
type User = z.infer<typeof UserSchema>  // derive type from schema — source of truth
```

## Branded Types (prevent ID mix-ups)

```ts
type UserId    = string & { readonly _brand: 'UserId' }
type ProductId = string & { readonly _brand: 'ProductId' }

function createUserId(raw: string): UserId { return raw as UserId }

// Now TS will error if you pass a ProductId where UserId is expected
function getUser(id: UserId): Promise<User> { ... }
```

## const satisfies (type narrowing without losing inference)

```ts
const palette = {
  brand: '#9B7FE8',
  surface: '#0F0F17',
} satisfies Record<string, string>
// palette.brand is typed as '#9B7FE8' (literal), not string
```

## Error Handling Pattern (typed errors)

```ts
type AppError =
  | { type: 'NOT_FOUND'; resource: string }
  | { type: 'UNAUTHORIZED' }
  | { type: 'VALIDATION'; fields: Record<string, string[]> }

type ActionResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: AppError }

async function getUser(id: string): Promise<ActionResult<User>> {
  const user = await db.user.findUnique({ where: { id } })
  if (!user) return { ok: false, error: { type: 'NOT_FOUND', resource: 'User' } }
  return { ok: true, data: user }
}
```

## Anti-Patterns to Avoid
- `as any` — use `unknown` + type guard instead
- Casting with `as T` without validation — use Zod or a type guard
- Over-engineering types for internal implementation — keep them simple
- Re-declaring types from Prisma — import `Prisma.UserGetPayload<{}>` instead
