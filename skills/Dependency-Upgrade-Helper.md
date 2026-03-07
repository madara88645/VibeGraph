# Dependency Upgrade Helper
Use for this: Plan and execute safe dependency upgrades with validation and rollback strategy.

Constraints: Never suggest major version upgrades without listing breaking changes. Always test after upgrading.
Agent note: Check the library's actual changelog. Don't assume — verify compatibility ranges.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Upgrade Process

### Step 1: Audit Current State
```bash
# Check for vulnerabilities
npm audit --audit-level=moderate
pnpm audit

# See what's outdated
npm outdated
npx npm-check-updates  # shows available upgrades

# Check peer dependency conflicts
npm install --dry-run
```

### Step 2: Categorize Upgrades
| Type | Risk | Approach |
|---|---|---|
| **Patch** (1.0.0 → 1.0.1) | Very Low | Upgrade batch, run tests |
| **Minor** (1.0.0 → 1.1.0) | Low | Upgrade batch, check changelog |
| **Major** (1.0.0 → 2.0.0) | High | Upgrade one at a time, read full migration guide |
| **Security fix** | Varies | Upgrade immediately regardless of version |

### Step 3: Upgrade Strategy

#### Safe Batch (patch + minor)
```bash
# Upgrade all patch + minor at once
npx npm-check-updates -u --target minor
npm install
npm test
```

#### Major Version (one at a time)
```bash
# Example: upgrading react-query v4 → v5
npm install @tanstack/react-query@latest
# Read: https://tanstack.com/query/v5/docs/framework/react/guides/migrating-to-v5
# Fix breaking changes
# Run: npm test
# Commit: git commit -m "chore: upgrade react-query to v5"
```

### Step 4: Validation Checklist
After every upgrade:
- [ ] `npm install` completes without errors
- [ ] `pnpm typecheck` / `tsc --noEmit` passes
- [ ] `pnpm lint` passes
- [ ] `pnpm test` passes
- [ ] `pnpm build` succeeds
- [ ] Critical paths smoke-tested manually

### Step 5: Rollback if Needed
```bash
# Option 1: Revert package.json manually and reinstall
git checkout package.json package-lock.json
npm install

# Option 2: Git revert the commit
git revert [commit-hash]
```

---

## Common Major Upgrades Reference

### React 18 → 19
- [ ] `ReactDOM.render` → `createRoot` (already done in 18)
- [ ] Server Components: new rules for `use client` / `use server`
- [ ] `useFormState` → `useActionState`
- [ ] `ref` now passed as prop (no `forwardRef` needed)

### Next.js 14 → 15
- [ ] `params` is now a Promise: `const { id } = await params`
- [ ] `searchParams` is now a Promise too
- [ ] Caching defaults changed (now `no-store` by default for fetch)
- [ ] Check `next.config.ts` for deprecated options

### Prisma 5 → 6
- [ ] `findUnique` + `findFirst` now throw on not found (use `findUniqueOrThrow`)
- [ ] `@db.DateTime` deprecated for some providers
- [ ] Check driver adapters if using edge runtime

### Tailwind CSS v3 → v4
- [ ] PostCSS config changes (new plugin system)
- [ ] `@apply` behavior changes in some cases
- [ ] `darkMode: 'class'` → `darkMode: 'selector'`
- [ ] Custom config moves to CSS `@theme` blocks

---

## Dependency Audit Report Template
```
UPGRADE AUDIT — [date]
Package: [name]
From: [current version]
To: [target version]

BREAKING CHANGES:
- [change 1]
- [change 2]

FILES AFFECTED:
- [file 1] — [what changes]
- [file 2]

TESTS TO ADD/UPDATE:
- [test scenario]

ESTIMATED EFFORT: [quick / half-day / full day]
RISK: Low / Medium / High
```
