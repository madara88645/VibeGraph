# AGENTS.md

## Cursor Cloud specific instructions

### Overview

VibeGraph is a Python + React monorepo. The backend (FastAPI) lives at the repo root; the frontend (React 19 / Vite) lives in `explorer/`.

### Running services (dev mode)

Two processes are needed:

| Service | Command | Port | Working dir |
|---------|---------|------|-------------|
| Backend | `python3 serve.py` | 8000 | `/workspace` |
| Frontend | `npm run dev` | 5173 | `/workspace/explorer` |

Set `OPENROUTER_API_KEY` in `.env` (copy from `.env.example`). Without a real key the app boots but AI features return errors. For tests, use `GROQ_API_KEY=dummy-key-for-ci` (CI parity).

### Lint / Test / Build commands

See `README.md` and `.github/workflows/ci.yml` for canonical commands. Quick reference:

**Backend:**
- Lint: `python3 -m ruff check . --select E,F --ignore E501,E402 --exclude tests/upload_cases`
- Format check: `python3 -m ruff format --check . --exclude tests/upload_cases`
- Type check: `python3 -m mypy . --ignore-missing-imports --python-version 3.12 --exclude tests --explicit-package-bases --disable-error-code=import-untyped`
- Tests: `GROQ_API_KEY=dummy-key-for-ci python3 -m pytest tests/ -v`
- Tests + coverage (CI parity): `GROQ_API_KEY=dummy-key-for-ci python3 -m pytest tests/ -v --cov=. --cov-report=xml`
- Security check (CI): `bandit -r . -x tests/,explorer/,node_modules/ -ll -ii`

**Frontend** (run from `explorer/`):
- Install (CI parity): `npm ci`
- Lint: `npm run lint`
- Tests (CI parity): `npx vitest run`
- Build: `npm run build`

### Non-obvious caveats

- `ruff`, `mypy`, and `pytest` are installed via pip but may not be on `$PATH`. Use `python3 -m ruff`, `python3 -m mypy`, `python3 -m pytest` to be safe.
- If `bandit` is not on `$PATH`, run it as `python3 -m bandit`.
- The Vite dev server proxies `/api` requests to `localhost:8000` (configured in `explorer/vite.config.js`), so the backend must be running first.
- No database or external services are needed beyond the OpenRouter API. All state is in-memory.
- The frontend uses `npm` (lockfile: `explorer/package-lock.json`). Use `npm ci` for deterministic installs.
- The backend reads `OPENROUTER_API_KEY` from the `.env` file at the repo root via `python-dotenv`. When restarting the backend with a new key, kill both the parent shell process and the child `python3 serve.py` process (uvicorn spawns a child).
- `explorer/public/graph_data.json` is a sample/seed file used by the frontend when no upload has been done. It may get overwritten during app usage — restore it with `git checkout` if the diff is unintentional.
