# State Management Patterns
Use for this: Choose and implement the right state management approach for local, server, global, and URL state.

Constraints: Don't add a state management library if React's built-ins are enough. Match complexity to need.
Agent note: Most UI state should be local (useState). Most server state should be handled by the framework (Server Components + SWR/TanStack Query).
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## State Type Decision Guide

| State Type | Where It Lives | Solution |
|---|---|---|
| UI state (open/closed, selected) | Component | `useState` |
| Form state | Component / Form | `useReducer`, React Hook Form |
| Server/async data | Cache | Server Components, SWR, TanStack Query |
| Shared UI state (2–3 components) | Common parent | Prop drilling + `useState` |
| Global app state (theme, auth) | App-wide | Context + `useState`, or Zustand |
| URL-driven state (filters, tabs) | URL params | `useSearchParams`, `useRouter` |
| Cross-tab state | Browser | `localStorage` + `storage` event |

## Local State — React (default)

```tsx
// Simple toggle
const [isOpen, setIsOpen] = useState(false)

// Complex state with reducer
type Action =
  | { type: 'SET_FILTER'; filter: string }
  | { type: 'RESET' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_FILTER': return { ...state, filter: action.filter }
    case 'RESET': return initialState
    default: return state
  }
}
const [state, dispatch] = useReducer(reducer, initialState)
```

## Server State — TanStack Query

```tsx
// Fetching
const { data, isLoading, error } = useQuery({
  queryKey: ['posts', filters],
  queryFn: () => fetchPosts(filters),
  staleTime: 1000 * 60 * 5,  // 5 min cache
})

// Mutation with optimistic update
const mutation = useMutation({
  mutationFn: (newPost: CreatePost) => createPost(newPost),
  onMutate: async (newPost) => {
    await queryClient.cancelQueries({ queryKey: ['posts'] })
    const previous = queryClient.getQueryData(['posts'])
    queryClient.setQueryData(['posts'], (old: Post[]) => [...old, { ...newPost, id: 'temp' }])
    return { previous }
  },
  onError: (_, __, context) => {
    queryClient.setQueryData(['posts'], context?.previous)
  },
  onSettled: () => queryClient.invalidateQueries({ queryKey: ['posts'] }),
})
```

## Global State — Zustand

```ts
// src/stores/ui-store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  setTheme: (theme: 'light' | 'dark') => void
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      theme: 'dark',
      sidebarOpen: true,
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
    }),
    { name: 'ui-preferences' }  // persisted to localStorage
  )
)
```

## URL State (filters, tabs, pagination)

```tsx
'use client'
import { useRouter, useSearchParams } from 'next/navigation'

function FilterBar() {
  const router = useRouter()
  const params = useSearchParams()
  const status = params.get('status') ?? 'all'

  function setFilter(value: string) {
    const next = new URLSearchParams(params.toString())
    next.set('status', value)
    router.push(`?${next.toString()}`)
  }

  return <Select value={status} onValueChange={setFilter} .../>
}
```

## Context (for auth/theme — avoid for frequently updating state)

```tsx
// contexts/auth-context.tsx
interface AuthContextType {
  user: User | null
  signOut: () => void
}
const AuthContext = createContext<AuthContextType | null>(null)

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
```

## Anti-Patterns to Avoid
- Context for high-frequency updates → causes unnecessary re-renders → use Zustand
- Global Zustand for server data → use TanStack Query instead
- `useEffect` to sync server data to state → fetch in Server Component / TanStack Query
- Storing derived data in state → derive from existing state in render
