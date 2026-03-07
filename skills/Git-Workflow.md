# Git Workflow
Use for this: Establish consistent branching, commit, and PR practices for team or solo projects.

Constraints: Keep branch names short and descriptive. Commits must be atomic (one logical change per commit).
Agent note: Never commit directly to `main`. Always use a feature branch. Squash before merging long-running branches.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Branch Strategy

```
main          → production (protected, requires PR + CI pass)
  └── develop → staging integration (optional for larger teams)
       └── feature/[ticket]-short-description
       └── fix/[ticket]-short-description
       └── chore/short-description
```

### Branch Naming
```bash
feature/42-user-profile-page      # new feature (with ticket number)
fix/78-broken-mobile-nav          # bug fix
chore/update-dependencies         # maintenance (no user-facing change)
hotfix/payment-webhook-timeout    # urgent production fix
```

## Commit Convention (Conventional Commits)

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types
| Type | Use For |
|---|---|
| `feat` | New feature (triggers minor version bump) |
| `fix` | Bug fix (triggers patch version bump) |
| `chore` | Maintenance (deps, config, build) |
| `docs` | Documentation only |
| `style` | Formatting (no logic change) |
| `refactor` | Refactoring without behavior change |
| `test` | Adding or fixing tests |
| `perf` | Performance improvement |
| `ci` | CI/CD configuration |

### Examples
```bash
feat(auth): add magic link login flow
fix(dashboard): prevent infinite re-render on filter change
chore: update Next.js to 15.1.0
docs: update README with new env variables
test(api): add integration tests for /api/posts
perf(images): add blur placeholder to above-fold hero image
```

## Daily Workflow

```bash
# Start new work
git checkout main && git pull
git checkout -b feature/42-short-description

# During work: commit often, atomically
git add -p                          # stage hunks, not whole files
git commit -m "feat(scope): message"

# Before PR: clean up history
git rebase -i origin/main          # squash WIP commits, fix messages

# Push
git push origin feature/42-short-description
```

## PR Template

```markdown
## What
[1-2 sentence summary of what changed]

## Why
[Ticket link or explanation of why this was needed]

## How
[Brief explanation of approach, especially if non-obvious]

## Testing
- [ ] Tests added/updated
- [ ] Tested locally
- [ ] Edge cases considered: [list them]

## Screenshots (if UI change)
[Before / After]

## Checklist
- [ ] Lint passes
- [ ] Type check passes
- [ ] No console.log left in code
- [ ] Env vars documented in .env.example if added
```

## Common Commands

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard uncommitted changes to a file
git checkout -- src/components/Foo.tsx

# Stash work in progress
git stash
git stash pop

# Cherry-pick a commit to another branch
git cherry-pick <commit-sha>

# Compare current branch with main
git diff main...HEAD

# Find when a bug was introduced
git bisect start
git bisect bad             # current is broken
git bisect good v1.0.0     # last known good
# git will checkout commits for you to test
```

## Merge vs Rebase

| Scenario | Approach |
|---|---|
| Feature branch → main | Squash merge (clean history) |
| Long-running feature → update with main | Rebase (linear history) |
| Hotfix → main | Direct merge + tag |
| Never do | `force push` to `main` |

## Git Hooks (optional, via Husky)

```bash
npx husky init
# .husky/pre-commit
npm run lint && npx tsc --noEmit

# .husky/commit-msg (enforce conventional commits)
npx commitlint --edit
```
