# Code Review — Strict & Actionable
Use for this: High-signal, prioritized code review focused on correctness, security, and maintainability.

Constraints: Reference specific files and line numbers. Every finding must have a concrete fix, not just a problem statement.
Agent note: Review what's changed, not the whole codebase. Prioritize by risk, not by personal style preference.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Review Framework

### Priority Levels
- **P0 — Block:** Bug, security issue, data loss risk. Must fix before merge.
- **P1 — Fix:** Significant tech debt, missing tests for critical logic, performance issue.
- **P2 — Improve:** Non-obvious code, duplication, naming issues.
- **P3 — Nit:** Style, minor clarity, optional improvements.

### What to Review (in order)
1. **Correctness** — does it do what it's supposed to do?
2. **Security** — auth checks, input validation, secrets exposed?
3. **Error handling** — what happens when it fails?
4. **Tests** — is critical logic covered?
5. **Performance** — N+1 queries, blocking operations, large payloads?
6. **Readability** — will next developer understand this in 6 months?

---

## Security Review Checklist (check every PR)
- [ ] No hardcoded secrets or credentials
- [ ] All API routes verify auth before accessing data
- [ ] User can only access their own data (check `where: { userId: session.user.id }`)
- [ ] All user inputs validated with Zod before use
- [ ] No `dangerouslySetInnerHTML` with unvalidated content
- [ ] No SQL string concatenation

## Common Finding Templates

### Missing Auth Check
```
P0 — SECURITY: Missing authentication check
FILE: src/app/api/projects/route.ts
ISSUE: GET /api/projects returns data without verifying session.
FIX:
  const session = await getServerSession()
  if (!session) return new Response('Unauthorized', { status: 401 })
```

### N+1 Query
```
P1 — PERFORMANCE: N+1 query in project list
FILE: src/app/api/projects/route.ts, line 24
ISSUE: Fetching members in a loop — 1 query per project.
FIX:
  // Before (N+1)
  const projects = await db.project.findMany()
  for (const p of projects) { p.members = await db.member.findMany({ where: { projectId: p.id } }) }

  // After (single query)
  const projects = await db.project.findMany({ include: { members: true } })
```

### Missing Error Handling
```
P1 — RELIABILITY: Unhandled promise rejection
FILE: src/hooks/useCreateProject.ts, line 12
ISSUE: await createProject() can throw — no catch or error state.
FIX:
  const { mutate, error } = useMutation(createProject, {
    onError: (err) => toast.error(err.message ?? 'Failed to create project'),
  })
```

### Missing Input Validation
```
P0 — SECURITY: User input used without validation
FILE: src/app/api/projects/route.ts
ISSUE: name from request body used directly in DB query.
FIX: Add Zod validation before using body:
  const parsed = CreateProjectSchema.safeParse(await req.json())
  if (!parsed.success) return Response.json({ error: parsed.error.flatten() }, { status: 400 })
```

### Missing Test Coverage
```
P1 — QUALITY: No tests for critical validation logic
FILE: src/lib/validations/project.ts
ISSUE: Schema has complex business rules but zero test coverage.
FIX: Add tests in src/lib/validations/project.test.ts covering:
  - valid inputs pass
  - empty name is rejected
  - name > 100 chars is rejected
  - invalid visibility enum is rejected
```

---

## Review Output Format

### Summary
```
FILES REVIEWED: X files, Y lines changed
STATUS: ✅ Approve / ⚠️ Approve with comments / 🚫 Request changes
CRITICAL ISSUES: [n]
```

### Findings
```
[PRIORITY]: [short title]
FILE: path/to/file.ts (line X)
ISSUE: [what's wrong]
FIX: [exact code or steps to fix]
```

### Positive Callouts (optional)
Good patterns worth noting for the team.

### What Was NOT Reviewed
State scope explicitly to avoid false security.
