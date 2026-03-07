# Release Notes Assistant
Use for this: Write clear, accurate release notes for users and developers from git history, PR descriptions, or a feature list.

Constraints: User-facing notes: no technical jargon, no internal IDs. Dev changelog: include PR numbers and migration steps.
Agent note: Verify change descriptions against actual code/PRs. Never reveal internal architecture or unreleased features.
Subagent note: If multi-agent support is available, use the appropriate subagent to research, review, or implement this skill's work instead of handling everything in a single pass.

## Input → Output Mapping

Provide any of these to get release notes:
- Git log: `git log --oneline v1.0.0..HEAD`
- PR titles and descriptions
- Feature list in plain text
- Jira / Linear ticket list

---

## Release Notes Structure

### Version Header
```markdown
## v[X.Y.Z] — [Month Day, Year]
```

### User-Facing Format (public changelog / app notification)
```markdown
## v2.4.0 — March 6, 2026

### ✨ New Features
- **Project Templates** — Start new projects from pre-built templates to save time.
- **Bulk Actions** — Select multiple items and archive, delete, or move them at once.

### 🔧 Improvements
- Dashboard loads 40% faster on large accounts.
- Search now includes project descriptions, not just titles.
- Better error messages when file uploads fail.

### 🐛 Bug Fixes
- Fixed: Comment notifications sent to wrong team members.
- Fixed: Dark mode toggle not saving preference across sessions.

### ⚠️ Breaking Changes
- API: `/api/v1/projects` endpoint deprecated. Migrate to `/api/v2/projects` by April 30.
```

### Developer Changelog (internal / GitHub release)
```markdown
## v2.4.0 — 2026-03-06

### Features
- feat: add project templates system (#234) @username
- feat: bulk action toolbar with multi-select (#241) @username

### Performance
- perf: optimize dashboard query with compound index (#238) @username

### Bug Fixes
- fix: incorrect recipient in comment notification emails (#239) @username
- fix: theme preference not persisted in localStorage (#243) @username

### Breaking Changes
- BREAKING: `/api/v1/projects` is deprecated. See migration guide below.

### Migration Guide (v1 → v2 API)
Old: GET /api/v1/projects?userId=123
New: GET /api/v2/projects (uses session auth, no userId param needed)
Timeline: v1 endpoint removed in v3.0 (Q3 2026)

### Dependencies Updated
- prisma: 5.8 → 5.10
- next: 15.0 → 15.1

### PRs Included
#233 #234 #238 #239 #241 #243
```

---

## Commit → Release Note Mapping
| Commit prefix | Release section |
|---|---|
| `feat:` | ✨ New Features |
| `fix:` | 🐛 Bug Fixes |
| `perf:` | 🔧 Improvements |
| `refactor:` | (internal only, skip user notes) |
| `BREAKING CHANGE:` | ⚠️ Breaking Changes |
| `chore:`, `ci:` | (skip) |
| `docs:` | (skip unless user-facing docs) |

---

## Quick Templates

### Hotfix release
```markdown
## v2.3.1 — March 6, 2026

### 🐛 Bug Fixes
- Fixed critical issue causing [symptom] for accounts with [condition].
  Affected: [who]. Timeframe: [when]. No data was lost.
```

### Major release
```markdown
## v3.0.0 — March 6, 2026

This is a major release with several breaking changes. Please review the
migration guide before upgrading.

### What's New
...

### Breaking Changes
...

### Full Migration Guide
[link to docs]
```
