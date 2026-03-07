# Feature Sketch
Use for this: Rapidly sketch a new feature's UI, data model, and interaction flow before implementation begins.

Constraints: Keep it lean — the sketch is for alignment, not specification. Ship the sketch in under 10 minutes.
Agent note: State assumptions clearly. Never recommend architectural changes without understanding the codebase.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Feature Sketch Template

### Feature: [Name]

**One-line description:**
> [What this feature does for the user in one sentence]

**User story:**
> As a [user type], I want to [action], so that [benefit].

---

### UI Sketch (Wireframe in Words)

```
┌────────────────────────────────────────┐
│  [Page Title]                    [CTA] │
├────────────────────────────────────────┤
│                                        │
│  [Primary content area]                │
│  - Item 1  [action button]             │
│  - Item 2  [action button]             │
│  - ...                                 │
│                                        │
│  [Empty state message if no items]     │
│                                        │
└────────────────────────────────────────┘
```

**States to design:**
- [ ] Loading (skeleton)
- [ ] Empty (friendly message + CTA)
- [ ] Populated (normal state)
- [ ] Error (with retry)
- [ ] Success feedback (toast or inline)

---

### Data Shape

**New entity (if any):**
```ts
interface [EntityName] {
  id:        string;
  [field]:   [type];   // [why this field]
  createdAt: Date;
  updatedAt: Date;
}
```

**API endpoints needed:**
```
GET    /api/[resource]         → list
POST   /api/[resource]         → create
GET    /api/[resource]/[id]    → get one
PUT    /api/[resource]/[id]    → update
DELETE /api/[resource]/[id]    → delete
```

**Query patterns:**
```ts
// What data is fetched and how often
useQuery(['resource', filters], () => fetchResource(filters))
useMutation(createResource, { onSuccess: () => invalidate(['resource']) })
```

---

### Key Interactions

| User Action | System Response | Notes |
|---|---|---|
| Click [CTA] | Open modal / Navigate | ... |
| Submit form | Optimistic add + API call | Show loading on button |
| Delete item | Confirm dialog → soft delete | Keep in DB for 30d |

---

### Implementation Notes

**Files to create:**
```
src/app/[route]/page.tsx          # Page
src/components/features/[Name]/   # Feature components  
src/lib/validations/[name].ts     # Zod schema
src/app/api/[resource]/route.ts   # API route
```

**Assumptions:**
- [Assumption 1 — mark if uncertain]
- [Assumption 2]

**Open questions (resolve before coding):**
1. [Question 1]
2. [Question 2]

**Risks:**
- [Risk 1: e.g., "Query could be slow if table grows large — add index on X"]
