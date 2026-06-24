# Server-Funded Free Trial — Design Spec

- **Date:** 2026-06-24
- **Status:** Approved (design), pending implementation plan
- **Owner:** Mehmet (madara88645)
- **Executor:** autonomous agent (Codex)
- **Track:** Monetization / "remove the BYO-key wall"

---

## 1. Goal & success test

> A brand-new visitor sees their **first AI explanation without entering any API key**, gets **5 free server-funded AI actions**, then hits a clear "add your own (free) key" wall.

**Success test (manual, in an incognito window):** open the site → click a node WITHOUT entering a key → an AI explanation renders. After 5 AI actions, a wall appears pointing to AI Settings.

This is the single highest-leverage monetization move: today `/api/ai-config` returns `requiresUserKey: true` with no server fallback, so every user must create an OpenRouter account + paste a key before ANY AI works — which destroys onboarding for the "vibe coder / junior dev" audience.

---

## 2. Current architecture (grounded)

- **The server-key plumbing already exists** in `app/dependencies.py`:
  - `resolve_openrouter_api_key(request)`: returns the bearer token if present; else the server key **if** `is_server_fallback_enabled()`; else raises 401.
  - `is_server_fallback_enabled()`: true only when `ALLOW_SERVER_FALLBACK_KEY` is truthy **and** `OPENROUTER_API_KEY` is set.
  - `get_public_ai_config()`: returns `requiresUserKey = not is_server_fallback_enabled()`.
  - `get_teacher_for_request(request, model)` is the single chokepoint every AI endpoint calls (`chat.py`, `explain.py`, `ghost.py`, `learning.py`).
- **No persistence**: the API is fully stateless (no DB, Redis, or volume). `app/rate_limit.py` already does **in-memory, IP-keyed** rate limiting via slowapi (`get_remote_address`) — we follow the same pattern.
- **Fly**: `min_machines_running = 0`, `auto_stop_machines = "stop"` → machines scale to zero and restart. In `fly.toml`, `ALLOW_SERVER_FALLBACK_KEY = "false"` today (feature off in prod).

**Implication:** we are NOT building key handling from scratch. We add a **metering layer** in front of the existing server-key path, plus a **frontend trial UX**. The feature stays fully inert until the owner sets the secret + flips the flag.

---

## 3. Design (recommended approach — Codex may improve)

> **Implementation latitude.** This section is **guidance, not a mandate**. Codex's model is strong and is trusted to make its own engineering calls — module/file names, exact field names, the counting mechanics, and the UX placement are all open to a better idea, **provided Section 4 (Acceptance Threshold) and Section 5 (Boundaries) hold unchanged**. Prefer the simplest design that passes the threshold; if you deviate from this section, say so and why in the PR description. **What is fixed:** the goal, the 10 acceptance criteria, and the boundaries. **What is yours to decide:** how you get there.

### 3.1 Backend

- **New module `app/services/trial_meter.py`** — an in-memory meter behind a small interface so a persistent backend (Upstash) can replace it later in one file:
  - `remaining(identity) -> int`
  - `consume(identity) -> int` (decrements, returns new remaining; never below 0)
  - Per-identity store: `IP -> used_count`; free allowance = `TRIAL_FREE_CALLS` (default **5**, env-overridable).
  - **Global daily cap**: an in-memory counter of total server-funded actions today; when it exceeds `TRIAL_GLOBAL_DAILY_CAP` (default e.g. **500/day**, env-overridable), the meter reports "exhausted" for everyone until the day rolls over (soft secondary guard; the hard guard is the OpenRouter credit limit).
  - Identity = client IP via the same helper slowapi uses (`get_remote_address`), to stay consistent and avoid new PII storage.

- **`app/dependencies.py`** — insert metering into the no-user-key branch of `resolve_openrouter_api_key()`:
  - user bearer token present → return it, **no metering** (existing behavior, unlimited).
  - else if `is_server_fallback_enabled()`:
    - if trial remaining for this identity AND global cap not hit → return server key + `consume(identity)`.
    - else → raise **402** with a clear message ("Free trial used up — add your own OpenRouter key in AI Settings.").
  - else → existing 401.
  - **Counting rule (MVP):** **one user-initiated AI action = one trial unit.** Consume once at the point the server key is granted per AI request (so a learning-path request that internally makes several model calls still costs **1** unit, not several). Acceptable slight over-count if the downstream AI call fails; refine to count-on-2xx only if cheap.
  - **Ghost narration is excluded from the trial**: ghost endpoints must not consume server-funded credits — they require the user's own key (prevents the known per-step cost-trap).

- **`/api/ai-config`** (`get_public_ai_config`) — add fields so the frontend knows when to show the wall:
  - `trialEnabled: bool` (true when server fallback is on)
  - `trialRemaining: int` (for this identity; the free allowance when fresh)
  - keep `requiresUserKey` meaning: a key is only *required* once the trial is unavailable/exhausted.

- **`X-Trial-Remaining` response header** on AI endpoints so the frontend updates the live counter without an extra round-trip.

### 3.2 Frontend (`explorer/`)

- **Live counter badge**: "X bedava hak kaldı" in the header / near AI panels, fed by `ai-config` + the `X-Trial-Remaining` header.
- **The wall**: when trial is unavailable (exhausted, or globally capped) and the user has no key, an AI action shows a friendly panel → opens `AISettingsModal` with copy: *"Bedava denemen bitti. Devam için ücretsiz OpenRouter key'ini ekle"* + the existing step-by-step key instructions.
- **Existing BYO flow** (`AISettingsModal.jsx`, `aiClient.js`) is unchanged for users who already have a key — never metered, no counter, no wall.
- Ghost Runner narration: gated behind "own key required" (since excluded from trial).

### 3.3 Cost safety (two layers)

1. **Code (Codex):** the in-memory global daily cap flips server-funding off for the rest of the day when exceeded → a viral spike cannot run away. Existing per-minute IP rate limits remain on top.
2. **Manual (owner):** a fixed **monthly credit limit on the OpenRouter key** (e.g. $10) is the hard ceiling.

---

## 4. Acceptance Threshold (Definition of Done)

> **This section is fixed and binding** — the contract for the autonomous run. Codex has full latitude on *how* (Section 3), but the goal is met only when **ALL** of the following are true (testable):

**Functional**
1. With `ALLOW_SERVER_FALLBACK_KEY=true` + a server key set, a fresh visitor (no user key) triggers an AI explanation and gets a valid result — **zero key input required**.
2. That visitor gets exactly **5** server-funded AI actions (explain + chat + learning-path combined); the **6th** is blocked with a clear **402** and the frontend wall pointing to AI Settings.
3. A live **"X bedava hak kaldı"** counter is visible, decrements correctly, and reads **0** at the wall.
4. A user who enters their **own** key is **never** metered (unlimited) and never sees the counter/wall — existing BYO behavior byte-for-byte unchanged.
5. **Ghost Runner narration does not consume trial credits** (requires own key).
6. When the global daily cap is exceeded, server-funding switches off (everyone falls back to BYO) with a clear message, no 500s.
7. With the flag **off** (current prod default), behavior is **identical to today** — feature fully inert, backward compatible.

**Quality gates**
8. All existing + new tests green (`pytest`), frontend tests green, `ruff` + `mypy` clean.
9. New tests cover: `TrialMeter` (consume / remaining / global cap / day rollover); `resolve_openrouter_api_key` trial branch (remaining→server key, exhausted→402, ghost excluded); `ai-config` trial fields; frontend counter + wall.
10. Codex **browser-verifies** criteria 1–3 end-to-end with a throwaway test key and reports evidence (screenshots + console/network).

**If all 10 hold, the task is DONE.** Do not expand scope beyond this.

---

## 5. Boundaries — Codex vs Owner

| Codex (autonomous, in-repo) | Owner (manual, out-of-repo) |
|---|---|
| All code, tests, the metering module | Create OpenRouter key + **set a monthly credit limit** |
| `ai-config` + `X-Trial-Remaining` header + frontend counter/wall | `fly secrets set OPENROUTER_API_KEY=…` |
| Docs + `.env.example` note + manual rollout checklist | Set `ALLOW_SERVER_FALLBACK_KEY=true` and deploy |
| Browser verification with a **throwaway test key** | Watch live spend |

**Codex must NOT:** set real secrets, flip the prod Fly env/flag, edit deploy/CI config, touch billing, change any AI prompt / response-format / temperature / max_tokens, or alter package-lock/dependencies unless strictly required (and call it out if so). The feature ships **off** and is enabled only by the owner's manual steps.

---

## 6. Out of scope (YAGNI)

Accounts, login, Stripe/payments, persistent DB/Redis, email, tiers. This task is **only** the server-funded free trial. (Managed-AI SaaS is a separate, later project.)

---

## 7. Manual rollout checklist (owner, after merge)

1. Create an OpenRouter API key; set a **monthly credit limit** (e.g. $10).
2. `fly secrets set OPENROUTER_API_KEY=<key>` on `vibegraph-api`.
3. Set `ALLOW_SERVER_FALLBACK_KEY=true` (Fly env) and deploy.
4. Incognito smoke test: node click without a key → explanation renders; 6th action → wall.
5. Watch OpenRouter spend for the first day.
