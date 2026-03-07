# Vibe Coding Playbook
Use for this: The team's shared playbook for fast, creative, high-quality coding sessions.

Constraints: Follow these rules to stay productive without accumulating debt.
Agent note: These are defaults — adjust per project, but don't drop the safety checks.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## The Vibe Coding Mindset
Vibe coding is **fast but not reckless**. The goal is maximum learning and momentum per unit of time, while keeping the codebase in a state you're not ashamed of on Monday morning.

**Speed comes from:**
- Clear scope before starting
- Agent specialization (right agent for right task)
- Mocking aggressively to avoid infra setup
- Committing working states every 15 minutes

**Quality comes from:**
- Types everywhere (no `any`)
- At least one test per critical path
- Error states always handled
- Never pushing broken code

---

## Session Rules

### Before Starting
- [ ] Goal is defined in one sentence
- [ ] Timebox is set (20 / 30 / 45 / 60 / 90 min)
- [ ] Minimum viable demo defined (3–5 bullet points)
- [ ] Agent assignments planned (VibePlanner output)
- [ ] Parking lot is empty (previous session items filed)

### During the Session
- [ ] Work in 15-minute sprint chunks
- [ ] Commit at end of every chunk: `git commit -m "wip: [what works]"`
- [ ] If blocked > 3 minutes → move on, leave `// TODO:` comment
- [ ] No scope additions without removing something else
- [ ] Call TempoCoordinator if behind schedule

### Before Ending
- [ ] Code compiles with no errors
- [ ] Critical path is manually testable
- [ ] `git push` completed
- [ ] Demo script written or updated
- [ ] Next session's parking lot updated

---

## Code Quality Floor (non-negotiable even in vibe sessions)

### TypeScript
```ts
// ❌ Never
const data: any = await fetch(...)
function process(input) { ... }

// ✅ Always
const data: Project[] = await fetch<Project[]>(...)
function process(input: ProjectInput): ProcessedProject { ... }
```

### State in Components
```tsx
// ❌ Never ship without all states
function ProjectList() {
  const { data } = useProjects()
  return data.map(p => <ProjectCard key={p.id} {...p} />)
}

// ✅ Always handle all states
function ProjectList() {
  const { data, isLoading, error } = useProjects()
  if (isLoading) return <ProjectListSkeleton />
  if (error) return <ErrorState message="Failed to load projects" onRetry={refetch} />
  if (!data?.length) return <EmptyState message="No projects yet" action="Create one" />
  return data.map(p => <ProjectCard key={p.id} {...p} />)
}
```

### API Routes
```ts
// Always: validate + auth + proper error format
export async function POST(req: Request) {
  const session = await auth(); if (!session) return unauthorized()
  const body = Schema.safeParse(await req.json())
  if (!body.success) return validationError(body.error)
  // ... logic
}
```

---

## 15-Minute Sprint Checklist
```
Sprint Goal:  [one specific outcome]
Agent:        [who's working]
Time:         [start → end]

5 min in:  [ ] Approach clear, not stuck
10 min in: [ ] Something working, small commit possible
15 min in: [ ] Done or decision made to cut scope
```

---

## When to Call for Help
| Situation | Action |
|---|---|
| Blocked on a technical decision | Ask Planner to re-scope |
| Time running out | Call TempoCoordinator for scope cut |
| Design unclear | Ask DesignCritic for quick judgment |
| Test is failing weirdly | RefactorMedic to simplify then Tester |
| Build is broken | Task 0: fix build before anything else |

---

## Vibe Session Example Plans

### 30-min: "Build a working form"
```
0–10m:  Coder A — API route + Zod schema
10–20m: Coder B — Form component + mutation
20–28m: TestRunner — smoke tests
28–30m: DemoPackager — quick README
```

### 60-min: "Ship a complete feature"
```
0–15m:  Coder A — DB schema + API routes (CRUD)
15–35m: Coder B — UI components + wiring
35–45m: UIStylist — visual polish
45–55m: Tester — unit + integration tests
55–60m: DemoPackager — demo bundle
```
