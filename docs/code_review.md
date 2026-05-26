# Code Review

**Date:** 2026-05-25
**Scope:** Entire repository (backend FastAPI, frontend Next.js, Docker, tests, docs)
**Reviewer:** Claude (Opus 4.7)

## Overall assessment

The project is a well-structured MVP that works end-to-end (25/25 tests pass; manual and AI flows verified). Separation of concerns is clear, schemas are typed, the backend has solid test coverage, and the frontend uses optimistic updates with server reconciliation. Secrets are kept out of git.

**Status (2026-05-25):** Both High findings, all six Medium findings, and L1/N4 have been resolved and verified — they are listed in the **Resolved** section at the end. The findings below are the remaining open items (Low severity and nits); none block use.

Severity: **High** = fix soon (correctness/reproducibility/security for any deployment) · **Medium** = should fix · **Low** = cleanup/polish · **Nit** = optional.

No High or Medium findings remain open.

---

## Open findings — Low

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

## Open findings — Nits

- **N1** `routes/ai.py`: `from ..schemas import CardUpdate` is separated from the other schema import — group them.
- **N2** `datetime.utcnow()` in `auth.py` is deprecated (3.12 warnings). Use `datetime.now(timezone.utc)`.
- **N3** `delete_card_db` commits twice (delete, then renumber). Could be a single transaction.

---

## Strengths (keep doing)

- Clear layering: routes -> shared DB helpers -> models; AI route reuses the same helpers.
- Typed Pydantic schemas and an explicit frontend mapping layer (`api.ts`) with prefixed dom ids that avoid dnd-kit id collisions.
- Optimistic UI with server reconciliation and a 401 self-heal.
- Structured AI outputs with per-mutation resilience (one bad mutation doesn't fail the reply).
- Good backend test coverage (auth, CRUD incl. move/renumber, AI mutations mocked); modernized E2E covering the real integrated flow.
- Secrets kept out of git; docs reconciled with code; corrupted `.gitignore` repaired.

---

## Remaining action checklist (Low / Nit)

1. [ ] (L2, L3) Remove unused `AIMessage` and password helpers.
2. [ ] (L4) Stop leaking exception text from the AI routes.
3. [ ] (L5) Move import-time side effects into `lifespan`.
4. [ ] (L6) Surface frontend write errors to the user.
5. [ ] (L7) Fix `KanbanBoard`'s `reload` effect deps (`useCallback`/inline).
6. [ ] (L8, L9) Add `.dockerignore`; drop `git` from the image.
7. [ ] (L10, L11) Add `api.ts` unit tests and a root `README.md`.
8. [ ] (N1–N3) Minor cleanups (import grouping, timezone-aware datetime, single-commit delete).

---

## Resolved (2026-05-25)

All High and Medium findings plus L1 and N4 were fixed and verified (25/25 tests pass: 16 backend, 6 frontend, 3 E2E). Details are in git history (commits `20f1ec3`, `30c5904`).

- **H1 — Duplicate DB module in `app/__init__.py`:** reduced to a package docstring; `database.py` is the single `Base`/engine source.
- **H2 — Clean-clone build:** `backend/static/` is now tracked, so the Docker image builds from a fresh clone without a manual frontend build.
- **M1 — CORS:** dropped `allow_credentials`; scoped `allow_origins` to `http://localhost:3000` / `http://127.0.0.1:3000`.
- **M2 — SECRET_KEY:** `config.py` warns when `SECRET_KEY` is unset instead of silently using the insecure default.
- **M3 — Dead auth code:** deleted `frontend/src/lib/auth.ts` (nothing imported it).
- **M4 — DATABASE_URL:** resolved in `config.py` (env override else computed SQLite path) and used by `database.py`.
- **M5 — Optimistic temp-id race:** `createCard` returns the saved card; `handleAddCard` swaps the temp id for the real server id (no full reload).
- **M6 — Board uniqueness:** added `unique=True` to `KanbanBoard.user_id`.
- **L1 — Emoji prints:** removed all emoji from startup output.
- **N4 — Card detail placeholder:** optimistic add no longer injects `"No details yet."`; it uses the entered details, consistent with the backend.
