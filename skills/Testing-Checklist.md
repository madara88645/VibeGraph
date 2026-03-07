# Testing Checklist
Use for this: Structured pre-merge and pre-release testing guidance for any feature.

Constraints: Risk-based — focus testing effort where bugs would hurt most.
Agent note: List concrete scenarios. Never claim coverage without data.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Testing Priority Matrix

| Risk Level | Feature Type | Testing Required |
|---|---|---|
| **Critical** | Auth, payments, data deletion | Unit + Integration + E2E + Manual |
| **High** | Core CRUD, user-facing forms | Unit + Integration + Manual smoke |
| **Medium** | UI components, display logic | Unit + Visual check |
| **Low** | Copy changes, icon swaps | Manual smoke only |

## Per-Feature Testing Checklist

### Unit Tests (fastest, most value per minute)
- [ ] Pure functions tested with valid input
- [ ] Pure functions tested with invalid/edge input
- [ ] Validation logic (Zod schemas) tested
- [ ] Utility helpers tested
- [ ] No real DB/network calls in unit tests (use mocks)

```ts
// Example: testing a validation function
describe('validateEmail', () => {
  it('accepts valid email', () => expect(validateEmail('a@b.com')).toBe(true))
  it('rejects missing @', () => expect(validateEmail('notanemail')).toBe(false))
  it('rejects empty string', () => expect(validateEmail('')).toBe(false))
})
```

### Integration Tests (medium speed, high confidence)
- [ ] API route returns 200 with valid input
- [ ] API route returns 400 with invalid input
- [ ] API route returns 401 when unauthenticated
- [ ] API route returns 403 when accessing another user's resource
- [ ] DB queries return expected data shape
- [ ] Side effects fire (email sent, queue message created)

```ts
// Example: testing an API route
it('POST /api/projects returns 401 when not authenticated', async () => {
  const res = await fetch('/api/projects', { method: 'POST', body: JSON.stringify({ name: 'Test' }) })
  expect(res.status).toBe(401)
})
```

### Component Tests (React Testing Library)
- [ ] Renders without throwing
- [ ] Renders loading state correctly
- [ ] Renders empty state correctly
- [ ] Renders error state correctly
- [ ] Primary action (click, submit) works
- [ ] Keyboard interaction works

```ts
// Example: component test
it('shows loading skeleton when isLoading=true', () => {
  render(<ProjectList isLoading />)
  expect(screen.getByTestId('skeleton')).toBeInTheDocument()
  expect(screen.queryByRole('listitem')).not.toBeInTheDocument()
})
```

### E2E Tests (Playwright — for critical flows only)
- [ ] User can sign up and log in
- [ ] User can complete the primary action (create/edit/delete main entity)
- [ ] User sees correct error when action fails
- [ ] User can log out

```ts
// Example: E2E test
test('user can create a project', async ({ page }) => {
  await page.goto('/dashboard')
  await page.getByRole('button', { name: 'New Project' }).click()
  await page.getByLabel('Project name').fill('My Project')
  await page.getByRole('button', { name: 'Create' }).click()
  await expect(page.getByText('My Project')).toBeVisible()
})
```

### Manual Smoke Tests (before every demo/release)
- [ ] Page loads without console errors
- [ ] Primary user flow completes end-to-end
- [ ] Mobile layout is not broken (375px)
- [ ] Loading states appear during async operations
- [ ] Error states display correctly
- [ ] Network tab shows expected requests (no 4xx/5xx)

## Commands
```bash
pnpm test              # all unit + integration tests
pnpm test --coverage   # with coverage report
pnpm test:e2e          # E2E (Playwright)
pnpm typecheck         # TypeScript
pnpm lint              # ESLint
```

## Coverage Targets (guidelines, not rules)
- Critical paths: 90%+
- Business logic: 80%+
- UI components: 60%+
- Overall project: 70%+
