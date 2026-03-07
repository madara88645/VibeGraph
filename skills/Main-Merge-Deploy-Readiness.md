# Main Merge & Deploy Readiness
Use for this: Final preflight before comparing against `main`, opening or updating a PR, merging, pushing to `main`, and deploying.

Constraints: Use this only after implementation is finished. Do not treat unresolved warnings, failing tests, or unclear rollout risks as "good enough".
Agent note: This skill is the last gate. Compare the branch with `origin/main`, verify change scope, then confirm merge/push readiness and deploy readiness separately.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Goal
Create a repeatable end-of-work check so the branch is safe to:
- compare with `main`
- open or update a PR
- merge or push to `main`
- deploy without obvious breakage or missing steps

## Required Order

1. Sync with remote state
2. Compare branch vs `origin/main`
3. Verify code quality and test health
4. Verify config, migrations, and environment readiness
5. Review deploy impact and rollback path
6. Produce a clear final verdict

## 1) Sync With Remote

```bash
git fetch origin
git status
git branch --show-current
```

Checks:
- Working tree is clean or intentionally staged
- You know the current branch name
- `origin/main` is up to date locally

## 2) Compare Against Main

```bash
# Files changed vs main
git diff --name-status origin/main...HEAD

# Full diff summary
git diff --stat origin/main...HEAD

# Commits on current branch not in main
git log --oneline origin/main..HEAD

# Commits in main not in current branch
git log --oneline HEAD..origin/main
```

Review questions:
- Does the changed file list match the intended task?
- Are there accidental files, debug changes, or unrelated edits?
- Is `main` ahead in a way that requires rebase or merge before shipping?
- Does the diff include generated files, snapshots, or migrations that must be reviewed carefully?

## 3) Quality Gate

Run the project-specific checks that matter for this repo.

```bash
# Example baseline
npm run lint
npx tsc --noEmit
npm test
npm run build
```

If applicable, also run:

```bash
# E2E / integration / storybook / package checks
npm run test:e2e
npm run test:integration
npm run storybook
```

Minimum pass criteria:
- No failing lint errors
- No type errors
- No failing required tests
- Production build succeeds
- No known critical manual regression left unchecked

## 4) Config, Schema, and Environment Check

Confirm whether the branch changed any of these:
- environment variables
- database schema or migrations
- auth/session behavior
- external service configuration
- feature flags
- build or deploy scripts

Checklist:

```text
[ ] New env vars documented in .env.example or deployment system
[ ] Removed env vars also removed from docs / platform config
[ ] Migrations reviewed and safe to apply
[ ] Seed / backfill / cron impacts identified
[ ] Auth or permission changes manually verified
[ ] No secret leaked into code, docs, logs, or sample files
```

## 5) Deploy Readiness

Deployment questions:
- Can this deploy without manual intervention?
- If manual intervention is needed, is it documented clearly?
- Could this break existing traffic, sessions, or background jobs?
- Is there a rollback path if deploy fails?

Pre-deploy checklist:

```text
[ ] Build artifacts are reproducible
[ ] Migration order is correct
[ ] Backward compatibility checked for APIs and DB
[ ] Feature flags default to safe values
[ ] Monitoring / logs / alerts are sufficient for this change
[ ] Rollback plan is known
[ ] Release note or deploy note prepared if needed
```

## 6) Push / Merge Readiness

Branch is ready to merge or push to `main` only if all are true:

```text
[ ] Diff vs origin/main matches intended scope
[ ] No unrelated files remain
[ ] Quality gate passed
[ ] Config and migration impact reviewed
[ ] Deploy checklist passed
[ ] Reviewer would understand the change from PR description / commits
[ ] Commit history is acceptable (or ready to squash)
```

## Common Stop Conditions
Do not mark as ready if any of these are true:
- `main` is ahead and introduces unresolved conflicts or behavior risk
- required tests were skipped without explicit justification
- migration or env changes exist but are undocumented
- rollback is unclear for a risky release
- diff contains unrelated refactors or accidental files
- production build was not verified

## Final Output Template

```text
MAIN COMPARISON
- Branch: [branch-name]
- Main baseline: origin/main
- Files changed: [count]
- Commits ahead of main: [count]
- Main ahead of branch: [yes/no + note]

QUALITY STATUS
- Lint: [pass/fail]
- Types: [pass/fail]
- Tests: [pass/fail/skipped with reason]
- Build: [pass/fail]

DEPLOY IMPACT
- Env changes: [none/list]
- Migrations: [none/list]
- Risk level: [low/medium/high]
- Rollback path: [clear/unclear]

FINAL VERDICT
- Ready for PR update: [yes/no]
- Ready to merge/push to main: [yes/no]
- Ready to deploy: [yes/no]

BLOCKERS
- [list blockers, or "none"]

NEXT ACTION
- [single best next step]
```

## Shortcut Rule
If the answer is not clearly "yes" for both merge readiness and deploy readiness, the final verdict is "not ready".