# Code Review

**Date:** 2026-05-25
**Scope:** Entire repository (backend FastAPI, frontend Next.js, Docker, tests, docs)
**Reviewer:** Claude (Opus 4.7)

## Overall assessment

The project is a well-structured MVP that works end-to-end (25/25 tests pass; manual and AI flows verified). Separation of concerns is clear, schemas are typed, the backend has solid test coverage, and the frontend uses optimistic updates with server reconciliation. Secrets are kept out of git.

The findings below were mostly hardening and cleanup. **Update (2026-05-25):** both High findings, all six Medium findings, and L1/N4 are now resolved and verified (25/25 tests pass: 16 backend, 6 frontend, 3 E2E). Remaining open items are Low/Nit. Resolved findings are tagged _(resolved)_ below; see the checklist at the end.

Severity: **High** = fix soon (correctness/reproducibility/security for any deployment) · **Medium** = should fix · **Low** = cleanup/polish · **Nit** = optional.

---

## High

### H1 — Duplicate database module in `backend/app/__init__.py` _(resolved 2026-05-25)_
`backend/app/__init__.py` is a near-verbatim copy of `backend/app/database.py`: it defines its own `engine`, `SessionLocal`, `Base`, `init_db`, and `get_db`. The whole app imports from `app.database`, so this copy is currently dead — but it creates a **second `Base` and engine**. If any module ever does `from app import Base` (instead of `from app.database import Base`), its models register on the wrong `Base` and tables silently won't be created. Confusing and dangerous.

**Action:** Reduce `app/__init__.py` to empty (or a one-line package docstring). Keep `database.py` as the single source.
**Done:** `__init__.py` reduced to a package docstring; `database.py` is the single `Base`/engine source.

### H2 — Image cannot be built from a clean clone _(resolved 2026-05-25)_
`backend/static/` is gitignored (it is a build artifact), but the `Dockerfile` does `COPY backend/static /app/static`. A fresh `git clone` has no `static/`, so `docker compose build` fails. Local builds only work because `static/` happens to exist on this machine.

**Action (pick one):**
- Preferred: make the `Dockerfile` multi-stage — a `node` stage runs `npm ci && npm run build` and produces the export, a `python` stage serves it. The repo then builds reproducibly with no manual step.
- Or: commit `backend/static/` (un-ignore it) so the repo is self-contained.
- Or (minimum): document the required `npm run build` + copy step in README and `CLAUDE.md`, and make the build fail loudly if `static/` is missing.

**Done:** Chose option 2 — `backend/static/` is now tracked, so the image builds from a clean clone. (A multi-stage build is a sound future improvement but was avoided here because `npm run build` needs network font access that this environment intercepts at the TLS layer.)

---

## Medium

### M1 — CORS is misconfigured and over-permissive _(resolved 2026-05-25)_
`backend/app/main.py` sets `allow_origins=["*"]` together with `allow_credentials=True`. That combination is invalid per the CORS spec (browsers refuse credentialed wildcard requests). The app is served same-origin and authenticates with a Bearer token, so wildcard CORS is unnecessary.

**Action:** Drop `allow_credentials=True`, and either remove the CORS middleware (same-origin needs none) or restrict `allow_origins` to known dev origins (e.g. `http://localhost:3000`).
**Done:** Scoped `allow_origins` to `http://localhost:3000` / `http://127.0.0.1:3000`; dropped `allow_credentials`.

### M2 — JWT secret silently falls back to a hardcoded default _(resolved 2026-05-25)_
`config.SECRET_KEY` defaults to `"dev-secret-key-change-in-production"` when `SECRET_KEY` is unset. A dropped `.env` line already caused a real "all requests 401" incident in this project, and for any non-local deployment the default is insecure.

**Action:** Fail fast (or log a prominent warning) when `SECRET_KEY` is unset outside local/dev. Document it as required in `.env.example` and `CLAUDE.md` (already noted there).
**Done:** `config.py` emits a `warnings.warn` when `SECRET_KEY` is unset (kept non-fatal so local runs and the test container still work).

### M3 — Dead, duplicated auth logic in the frontend _(resolved 2026-05-25)_
`frontend/src/lib/auth.ts` exports `useAuth`/`useRequireAuth`, but the pages (`app/page.tsx`, `app/kanban/page.tsx`) reimplement the same `localStorage` token checks inline. The hooks are unused.

**Action:** Either adopt the hooks across the pages, or delete `lib/auth.ts`. Pick one source of truth for auth/redirect logic.
**Done:** Deleted `lib/auth.ts` (confirmed nothing imported it); the pages' inline checks remain the single source.

### M4 — `database.py` ignores `DATABASE_URL` _(resolved 2026-05-25)_
The SQLite path is hardcoded in `database.py`, even though `.env`, `.env.example`, and `docker-compose.yml` all define `DATABASE_URL`. The env var is misleading because it has no effect.

**Action:** Read `DATABASE_URL` from config (fall back to the computed path), or remove `DATABASE_URL` from `.env`/compose to avoid implying it works.
**Done:** `DATABASE_URL` is resolved in `config.py` (env override, else computed SQLite path) and consumed by `database.py`.

### M5 — Optimistic temp-id race on new cards _(resolved 2026-05-25)_
A card added optimistically gets a client temp id (`card-<random>`). If the user moves/edits/deletes it before the create round-trip finishes, `numericId()` yields `NaN`, producing `PATCH /api/cards/NaN` (422). The change self-reverts via the error reload, so no data corruption, but the action silently fails. (Caught by E2E; see logs `PATCH /api/cards/NaN -> 422`.)

**Action:** Have `createCard` return the created card and swap the temp id for the real id in state (instead of, or before, the full reload). Alternatively disable per-card actions until the card has a numeric id.
**Done:** `createCard` now returns the saved card; `handleAddCard` swaps the temp id for the real server id in state (no full reload). The remaining window is just the create round-trip itself.

### M6 — No uniqueness on `KanbanBoard.user_id` _(resolved 2026-05-25)_
The model indexes but does not mark `user_id` unique (the schema docs say it should be unique — "one board per user"). `get_or_create_board` is read-then-create with no constraint, so a concurrent first request could create two boards.

**Action:** Add `unique=True` to `KanbanBoard.user_id`. Low risk today (single user), but it matches the intended invariant and prevents duplicates.
**Done:** Added `unique=True` to `KanbanBoard.user_id`.

---

## Low

### L1 — Emojis in `print()` violate the project style rule _(resolved 2026-05-25)_
`backend/app/database.py`, `app/main.py`, and `app/__init__.py` print emoji (`🚀`, `🛑`, `✓`). The root `AGENTS.md` states "no emojis ever."

**Action:** Remove the emojis; prefer the `logging` module over `print` for startup messages, or drop them.
**Done:** Removed all emoji startup prints (the `database.py`/`__init__.py` ones were dropped with those rewrites; `main.py` lifespan messages de-emojied).

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
- **N4** _(resolved 2026-05-25)_ The optimistic add no longer injects a `"No details yet."` placeholder; it uses the entered details, consistent with the backend.

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

> **Status (updated 2026-05-25):** H1, H2, M1–M6, L1, and N4 are resolved and verified
> (25/25 tests pass). Remaining items below are Low/Nit.

1. [x] (H1) Empty out `backend/app/__init__.py`; single `Base` in `database.py`.
2. [x] (H2) Track `backend/static/` so the image builds from a clean clone.
3. [x] (M1) Fix CORS: dropped credentials, scoped origins to localhost dev.
4. [x] (M2) Warn when `SECRET_KEY` is unset (insecure default).
5. [x] (M3) Removed dead `lib/auth.ts`.
6. [x] (M4) Honor `DATABASE_URL` (resolved in `config.py`).
7. [x] (M5) Reconcile optimistic temp ids with server ids in `handleAddCard`.
8. [x] (M6) Added `unique=True` to `KanbanBoard.user_id`.
9. [x] (L1) Removed emoji prints.
10. [ ] (L2, L3) Remove unused `AIMessage` and password helpers.
11. [ ] (L4) Stop leaking exception text from the AI routes.
12. [ ] (L5) Move import-time side effects into `lifespan`.
13. [ ] (L6) Surface frontend write errors to the user.
14. [ ] (L8, L9) Add `.dockerignore`; drop `git` from the image.
15. [ ] (L10, L11) Add `api.ts` unit tests and a root `README.md`.
