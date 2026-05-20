# Jules — VibeGraph

**Read before any task:** [AGENTS.md](../AGENTS.md) and [README.md](../README.md).

## What `.jules/` is

| File | Role |
|------|------|
| `instructions.md` | **Authoritative** rules for Jules |
| `bolt.md` | Performance learnings (React Flow, graph simulation, Python AST) |
| `palette.md` | UX / accessibility learnings |
| `sentinel.md` | Security learnings |

Journal files are **not** a mandatory refactor list. Do not sweep the repo applying every historical entry.

## Architecture

- **Backend:** FastAPI at repo root (`python3 serve.py`, port 8000).
- **Frontend:** React 19 + Vite in `explorer/` (`npm run dev`, port 5173).
- **State:** In-memory; no database. `explorer/public/graph_data.json` is seed data — do not overwrite unintentionally.

## Hard rules

1. **Scope:** Change only what the current task needs. No unrelated performance or a11y drive-bys.
2. **API keys:** `OPENROUTER_API_KEY` in root `.env`. CI/tests use `GROQ_API_KEY=dummy-key-for-ci`. Never log or commit secrets.
3. **Commands:** Prefer `python3 -m ruff`, `python3 -m pytest`, `python3 -m mypy` (tools may not be on bare `$PATH`).
4. **React Flow:** Preserve node/edge object references when only a subset of props change (see `bolt.md`); do not blanket-memo the whole graph.
5. **Contradictions:** If a `bolt.md` note conflicts with measured behavior on the path you are editing, trust the task + AGENTS.md, not the journal.

## When appending a learning

```markdown
## YYYY-MM-DD - Short title
**Learning:** ...
**Action:** ...
```

Never leave `<<<<<<<` / `=======` / `>>>>>>>` markers in any `.jules` file.

## Verification (from AGENTS.md)

**Backend:** `GROQ_API_KEY=dummy-key-for-ci python3 -m pytest tests/ -v` · `python3 -m ruff check .` · `python3 -m mypy .` (use `python3 -m` prefix if tools not on PATH).

**Frontend** (`explorer/`): `npm ci` · `npx vitest run` · `npm run lint` · `npm run build`.

**Security (CI):** `python3 -m bandit -r . -x tests/,explorer/,node_modules/ -ll -ii`
