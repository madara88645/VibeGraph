# Bug Triage Guide
Use for this: Quickly categorize, prioritize, and route incoming bug reports.

Constraints: Keep triage fast — under 5 minutes per bug. Always require a reproduction before assigning priority.
Agent note: Never assume root cause without reproduction. Mark uncertain items as "Needs Investigation."
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Severity Matrix

| Severity | Definition | SLA |
|---|---|---|
| **S1 — Critical** | Production down, data loss, security breach | Fix immediately |
| **S2 — High** | Core feature broken for all/most users | Fix this sprint |
| **S3 — Medium** | Feature degraded, workaround exists | Fix next sprint |
| **S4 — Low** | Minor UX issue, cosmetic, edge case | Backlog |

## Triage Steps (follow in order)

### Step 1: Reproduce
**Never assign priority without reproducing first.**
```
Environment:  [ ] Local  [ ] Staging  [ ] Production
Browser/OS:   _______________
Steps:
  1. _______________
  2. _______________
Expected:     _______________
Actual:       _______________
Screenshot?   [ ] Yes  [ ] No
```

### Step 2: Assess Impact
- How many users affected? (1 / some / most / all)
- Is there a workaround? (Yes / No)
- Does it involve data loss or security? (Yes → S1 immediately)
- Is it blocking a demo or release? (Yes → S2 minimum)

### Step 3: Assign Severity
Use the matrix above. When in doubt, go **one severity higher** (safer to over-prioritize a bug).

### Step 4: Route
```
S1 → Page on-call engineer, create war room
S2 → Assign to current sprint, notify team lead
S3 → Add to sprint backlog with full reproduction
S4 → Add to product backlog, link to affected component
```

### Step 5: Write the Bug Report
```markdown
## [SHORT_TITLE]

**Severity:** S1 / S2 / S3 / S4
**Environment:** Production / Staging / Local
**Affected Users:** All / Most / Some / One

### Reproduction Steps
1. Go to [URL]
2. Click [X]
3. Observe [Y]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Possible Cause (if known)
[Hypothesis — mark as unverified]

### Acceptance Criteria for Fix
- [ ] [Specific testable criteria]
- [ ] Regression test added
```

## Common Bug Categories & First Suspects

| Category | First Places to Look |
|---|---|
| UI broken on mobile | CSS breakpoints, `overflow: hidden`, viewport meta |
| Auth/login issue | Cookie expiry, session invalidation, CORS |
| Data not saved | Network tab (request/response), validation errors |
| Performance regression | Bundle size, N+1 queries, missing memoization |
| Race condition | Async state updates, missing `await`, optimistic UI |
| 3rd party API failure | Status page of service, rate limits, API key expiry |
