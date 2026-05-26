# Code Review

**Date:** 2026-05-25
**Scope:** Entire repository (backend FastAPI, frontend Next.js, Docker, tests, docs)
**Reviewer:** Claude (Opus 4.7)

## Overall assessment

The project is a well-structured MVP that works end-to-end (25/25 tests pass; manual and AI flows verified). Separation of concerns is clear, schemas are typed, the backend has solid test coverage, and the frontend uses optimistic updates with server reconciliation. Secrets are kept out of git.

The findings below are mostly hardening and cleanup. Two are worth doing soon: a duplicated database module (latent footgun) and the fact that the image cannot be built from a clean clone. None block local use today.

Severity: **High** = fix soon (correctness/reproducibility/security for any deployment) · **Medium** = should fix · **Low** = cleanup/polish · **Nit** = optional.

---

## High

### H1 — Duplicate database module in `backend/app/__init__.py`
`backend/app/__init__.py` is a near-verbatim copy of `backend/app/database.py`: it defines its own `engine`, `SessionLocal`, `Base`, `init_db`, and `get_db`. The whole app imports from `app.database`, so this copy is currently dead — but it creates a **second `Base` and engine**. If any module ever does `from app import Base` (instead of `from app.database import Base`), its models register on the wrong `Base` and tables silently won't be created. Confusing and dangerous.

**Action:** Reduce `app/__init__.py` to empty (or a one-line package docstring). Keep `database.py` as the single source.

### H2 — Image cannot be built from a clean clone
`backend/static/` is gitignored (it is a build artifact), but the `Dockerfile` does `COPY backend/static /app/static`. A fresh `git clone` has no `static/`, so `docker compose build` fails. Local builds only work because `static/` happens to exist on this machine.

**Action (pick one):**
- Preferred: make the `Dockerfile` multi-stage — a `node` stage runs `npm ci && npm run build` and produces the export, a `python` stage serves it. The repo then builds reproducibly with no manual step.
- Or: commit `backend/static/` (un-ignore it) so the repo is self-contained.
- Or (minimum): document the required `npm run build` + copy step in README and `CLAUDE.md`, and make the build fail loudly if `static/` is missing.

---

## Medium

### M1 — CORS is misconfigured and over-permissive
`backend/app/main.py` sets `allow_origins=["*"]` together with `allow_credentials=True`. That combination is invalid per the CORS spec (browsers refuse credentialed wildcard requests). The app is served same-origin and authenticates with a Bearer token, so wildcard CORS is unnecessary.

**Action:** Drop `allow_credentials=True`, and either remove the CORS middleware (same-origin needs none) or restrict `allow_origins` to known dev origins (e.g. `http://localhost:3000`).

### M2 — JWT secret silently falls back to a hardcoded default
`config.SECRET_KEY` defaults to `"dev-secret-key-change-in-production"` when `SECRET_KEY` is unset. A dropped `.env` line already caused a real "all requests 401" incident in this project, and for any non-local deployment the default is insecure.

**Action:** Fail fast (or log a prominent warning) when `SECRET_KEY` is unset outside local/dev. Document it as required in `.env.example` and `CLAUDE.md` (already noted there).

### M3 — Dead, duplicated auth logic in the frontend
`frontend/src/lib/auth.ts` exports `useAuth`/`useRequireAuth`, but the pages (`app/page.tsx`, `app/kanban/page.tsx`) reimplement the same `localStorage` token checks inline. The hooks are unused.

**Action:** Either adopt the hooks across the pages, or delete `lib/auth.ts`. Pick one source of truth for auth/redirect logic.

### M4 — `database.py` ignores `DATABASE_URL`
The SQLite path is hardcoded in `database.py`, even though `.env`, `.env.example`, and `docker-compose.yml` all define `DATABASE_URL`. The env var is misleading because it has no effect.

**Action:** Read `DATABASE_URL` from config (fall back to the computed path), or remove `DATABASE_URL` from `.env`/compose to avoid implying it works.

### M5 — Optimistic temp-id race on new cards
A card added optimistically gets a client temp id (`card-<random>`). If the user moves/edits/deletes it before the create round-trip finishes, `numericId()` yields `NaN`, producing `PATCH /api/cards/NaN` (422). The change self-reverts via the error reload, so no data corruption, but the action silently fails. (Caught by E2E; see logs `PATCH /api/cards/NaN -> 422`.)

**Action:** Have `createCard` return the created card and swap the temp id for the real id in state (instead of, or before, the full reload). Alternatively disable per-card actions until the card has a numeric id.

### M6 — No uniqueness on `KanbanBoard.user_id`
The model indexes but does not mark `user_id` unique (the schema docs say it should be unique — "one board per user"). `get_or_create_board` is read-then-create with no constraint, so a concurrent first request could create two boards.

**Action:** Add `unique=True` to `KanbanBoard.user_id`. Low risk today (single user), but it matches the intended invariant and prevents duplicates.

---

## Low

### L1 — Emojis in `print()` violate the project style rule
`backend/app/database.py`, `app/main.py`, and `app/__init__.py` print emoji (`🚀`, `🛑`, `✓`). The root `AGENTS.md` states "no emojis ever."

**Action:** Remove the emojis; prefer the `logging` module over `print` for startup messages, or drop them.

### L2 — Unused `AIMessage` model/table
`AIMessage` is defined and its table is created, but nothing reads or writes it (chat history is client-managed). Dead schema.

**Action:** Remove `AIMessage`, or implement server-side history persistence if that feature is wanted.

### L3 — Unused password hashing helpers
`hash_password`/`verify_password` in `auth.py` are never called; login compares hardcoded plaintext and stores an empty `password_hash`. (Pulls in `passlib[bcrypt]` for nothing.)

**Action:** Remove them (and the dependency) for MVP, or wire real hashing if multi-user becomes real.

### L4 — Internal exception text leaked to clients
`routes/ai.py` returns `detail=f"AI error: {exc}"`, exposing internal error strings (and potentially upstream details) to the client.

**Action:** Log the exception server-side; return a generic message (e.g. "AI request failed").

### L5 — Side effects at import time
`app/main.py` runs `Path("data").mkdir(...)` and `init_db()` at module import. Importing the app (e.g. in tests) has filesystem side effects.

**Action:** Move directory creation and `init_db()` into the `lifespan` startup handler.

### L6 — Frontend write failures are swallowed silently
Mutations use `.catch(reload)` / `.catch(() => {})` with no user-visible feedback (except the 401 redirect). A persistent backend failure looks like the change "just didn't stick."

**Action:** Surface a non-blocking error (toast/banner) when a write fails after reconciliation.

### L7 — Possible `react-hooks/exhaustive-deps` warning
`KanbanBoard` uses `useEffect(() => { reload(); }, [])` where `reload` is recreated each render.

**Action:** Wrap `reload` in `useCallback` and include it in deps, or inline the fetch in the effect.

### L8 — No `.dockerignore`
`COPY backend/ /app/` bakes `__pycache__/`, `tests/`, and `data/` (including `app.db`) into the image.

**Action:** Add a `.dockerignore` excluding `__pycache__/`, `*.pyc`, `data/`, and optionally `app/tests/`.

### L9 — `git` installed in the runtime image
The `Dockerfile` apt-installs `git`, which the runtime does not use.

**Action:** Remove `git` from the apt install line (keep `curl` for the healthcheck).

### L10 — Light frontend unit coverage
No unit tests for `lib/api.ts` (`mapBoard`/`numericId`), `AIChatSidebar`, card editing, or the move buttons.

**Action:** Add unit tests for `mapBoard`/`numericId` (pure, high-value) and a component test for edit/move handlers.

### L11 — No root `README.md`
Onboarding depends on `AGENTS.md`/`CLAUDE.md`/`docs`.

**Action:** Add a short root `README.md` (one-command run, default creds, link to `docs/`). Keep it minimal per the project's docs rule.

---

## Nits

- **N1** `routes/ai.py`: `from ..schemas import CardUpdate` is separated from the other schema import — group them.
- **N2** `datetime.utcnow()` in `auth.py` is deprecated (3.12 warnings). Use `datetime.now(timezone.utc)`.
- **N3** `delete_card_db` commits twice (delete, then renumber). Could be a single transaction.
- **N4** Optimistic add sets `details: details || "No details yet."`, but the backend stores empty description, so the placeholder disappears after reload. Minor visual inconsistency.

---

## Strengths (keep doing)

- Clear layering: routes -> shared DB helpers -> models; AI route reuses the same helpers.
- Typed Pydantic schemas and an explicit frontend mapping layer (`api.ts`) with prefixed dom ids that avoid dnd-kit id collisions.
- Optimistic UI with server reconciliation and a 401 self-heal.
- Structured AI outputs with per-mutation resilience (one bad mutation doesn't fail the reply).
- Good backend test coverage (auth, CRUD incl. move/renumber, AI mutations mocked); modernized E2E covering the real integrated flow.
- Secrets kept out of git; docs reconciled with code; corrupted `.gitignore` repaired.

---

## Prioritized action checklist

1. [ ] (H1) Empty out `backend/app/__init__.py`; single `Base` in `database.py`.
2. [ ] (H2) Make `Dockerfile` multi-stage (build frontend) or commit `backend/static/`; ensure clean-clone build works.
3. [ ] (M1) Fix CORS: drop wildcard+credentials; scope or remove.
4. [ ] (M2) Require `SECRET_KEY` outside dev (fail fast / warn).
5. [ ] (M3) Remove or adopt `lib/auth.ts` (one auth source).
6. [ ] (M4) Honor `DATABASE_URL` (or remove it from config).
7. [ ] (M5) Reconcile optimistic temp ids with server ids in `handleAddCard`.
8. [ ] (M6) Add `unique=True` to `KanbanBoard.user_id`.
9. [ ] (L1) Remove emoji prints / switch to logging.
10. [ ] (L2, L3) Remove unused `AIMessage` and password helpers.
11. [ ] (L4) Stop leaking exception text from the AI routes.
12. [ ] (L5) Move import-time side effects into `lifespan`.
13. [ ] (L6) Surface frontend write errors to the user.
14. [ ] (L8, L9) Add `.dockerignore`; drop `git` from the image.
15. [ ] (L10, L11) Add `api.ts` unit tests and a root `README.md`.
