# Prototype Boilerplate
Use for this: Scaffold a minimal, runnable project for fast experimentation and demos.

Constraints: Keep dependencies minimal. Don't add production configs (CI, Docker, monitoring) to a prototype.
Agent note: Ask which stack is preferred. Never assume a specific DB or auth service without asking.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Stack Options

### Option A: Next.js (fullstack, recommended for most prototypes)
```bash
npx create-next-app@latest my-proto --typescript --tailwind --app --no-src-dir --import-alias "@/*"
cd my-proto
npx shadcn@latest init -d  # default config, dark mode
npx shadcn@latest add button card input form badge
npm install lucide-react
npm run dev
```

**Add when needed:**
```bash
npm install @tanstack/react-query  # async state
npm install zustand                # global state
npm install zod                    # validation
npm install @prisma/client prisma  # DB
```

### Option B: Vite + React (frontend only, fastest start)
```bash
npm create vite@latest my-proto -- --template react-ts
cd my-proto
npm install
npm install -D tailwindcss autoprefixer postcss
npx tailwindcss init -p
npm install lucide-react
npm run dev
```

### Option C: T3 Stack (when you know you'll need auth + DB)
```bash
npm create t3-app@latest my-proto
# Select: Next.js + TypeScript + Tailwind + Prisma + NextAuth
cd my-proto
# Follow prompts
```

---

## Minimal File Structure (Next.js)

```
my-proto/
  app/
    layout.tsx           # Root layout with providers
    page.tsx             # Landing / entry point
    demo/
      page.tsx           # Main demo page
  components/
    ui/                  # shadcn components (auto-generated)
    [Feature].tsx        # Main demo component
  lib/
    mock-data.ts         # Hardcoded demo data
    utils.ts             # cn() helper + misc utils
  .env.local             # Local env vars (never commit)
  .env.example           # Template (safe to commit)
```

---

## Essential Starting Files

### `lib/mock-data.ts`
```ts
// All prototype data lives here — replace with real API later
export const MOCK_PROJECTS: Project[] = [
  {
    id: 'proj_1',
    name: 'Design System',
    status: 'active',
    members: 4,
    updatedAt: new Date('2026-03-01'),
  },
  // ... more items
]

export const MOCK_USER = {
  id: 'user_1',
  name: 'Alex Johnson',
  email: 'alex@example.com',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=alex',
}
```

### `lib/utils.ts`
```ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Simulate async delays for realistic loading states
export function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}
```

### `app/layout.tsx` (with providers)
```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import '@/app/globals.css'

const queryClient = new QueryClient()

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster />
        </QueryClientProvider>
      </body>
    </html>
  )
}
```

---

## Prototype Checklist
- [ ] `npm run dev` starts without errors
- [ ] Core flow is clickable end-to-end with mock data
- [ ] Loading states visible (even if `setTimeout` based)
- [ ] Error state visible (can be a static error screen)
- [ ] `// PROTO:` comments mark all temporary code
- [ ] `.env.example` is up to date
- [ ] `README.md` has one-command start instructions
