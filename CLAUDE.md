# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Project Management MVP: a single Kanban board per user with an AI chat sidebar that can create/edit/move/delete cards and rename columns. A Next.js frontend is statically exported and served by a FastAPI backend out of one Docker container. SQLite for storage, OpenRouter (model `openai/gpt-oss-120b`) for AI. Runs locally only.

`docs/PLAN.md` is the original execution plan (Parts 1-10); all parts are now implemented. `docs/API_SPEC.md` and `docs/DATABASE_SCHEMA.md` describe the original design and have drifted from the code in places — see "Data model and id mapping" below. **`backend/app/models.py` and `backend/app/schemas.py` are authoritative** when they disagree with the docs.

## Architecture

**One container, two responsibilities.** `backend/app/main.py` mounts the API under `/api/*` and serves the exported frontend at `/`. The `StaticFiles` mount is added after the routers so `/api/*` always wins. The static site is read from `backend/static/`.

**Auth.** Hardcoded credentials `user`/`password` (`routes/auth.py`) mint an HS256 JWT (`auth.py`). `get_current_user` in `auth.py` is the dependency protecting every `/api/kanban`, `/api/cards*`, `/api/columns*`, and `/api/ai/*` route; a missing or invalid token yields 401. The frontend stores the token in `localStorage` and redirects in client components.

**Board seeding.** On first authenticated board access, `get_or_create_board` (`routes/kanban.py`) creates the user's board with 5 columns and 8 demo cards. One board per user.

**Kanban CRUD** lives in `routes/kanban.py`, which also exposes the DB-mutation helpers (`create_card_db`, `update_card_db`, `delete_card_db`, `rename_column_db`, `serialize_board`) that the AI route reuses. Card order is a per-column integer `position`; moves and reorders renumber the affected columns to stay contiguous (`_renumber`). The session has `autoflush=False`, so a cross-column move flushes before re-querying the source column (a subtle correctness point — see the comment there).

**AI.** `app/ai.py` calls OpenRouter via the `openai` SDK using a strict `json_schema` response format (`gpt-oss-120b` supports structured outputs). `ai_chat` returns `{response, mutations}`. `routes/ai.py` applies each mutation through the kanban helpers — skipping any that reference a missing card/column so one bad suggestion doesn't fail the reply — then returns the response plus a freshly serialized `updated_board`. Conversation history is client-managed (sent in each request), not persisted server-side.

**Frontend data flow.** `src/lib/api.ts` is the API client and the single mapping layer. `KanbanBoard` initializes from `initialData` (so it paints instantly and the Vitest tests run without a backend), then `fetchBoard()` replaces it on mount. Every mutation updates local state optimistically and fires the API call; on error it calls `reload()` to re-sync from the server. The AI sidebar replaces board state from the `updated_board` in its response. Columns render in a horizontal scroll row; each card has ←/→ buttons (`handleMoveCard`) as a no-drag way to move between columns, alongside dnd-kit drag.

## Data model and id mapping

Authoritative source: `backend/app/models.py`. These differ from `docs/`:
- Tables are `users`, `kanban_boards`, `kanban_columns`, `kanban_cards`, `ai_messages` (the docs DDL says `columns`/`cards`).
- Columns and cards use `title` and integer `position` (docs say `name`/`order`); cards use `description`. The `ai_messages` table exists but is currently unused.

The API speaks `{id, title, position, ...}` (`schemas.py`). The frontend client maps that to the UI's `BoardData` shape from `src/lib/kanban.ts`, where column order and card order are implied by array order (`columns[]`, `cardIds[]`) and a card's body field is `details`. To avoid dnd-kit id collisions between equal column/card integer ids, dom ids are prefixed `col-<n>` / `card-<n>`; `numericId()` strips the prefix before API calls.

## Commands

Run the app (serves UI + API at http://localhost:8000):
```
docker compose up -d --build         # or scripts/start.* (sh/ps1/bat)
docker compose down                  # or scripts/stop.*
```
Health: `GET /api/health`. After editing `.env`, recreate the container — a plain restart does NOT reload `env_file`:
```
docker compose up -d --force-recreate
```

Frontend (`cd frontend`):
```
npm run dev          # dev server on :3000
npm run build        # static export -> frontend/out/
npm run test:unit    # vitest
npm run lint
```
Single unit test: `npx vitest run src/lib/kanban.test.ts` (or `-t "name"`).

In this environment Google Fonts is unreachable at build time, so `npm run build` fails fetching Manrope/Space Grotesk unless you set system TLS certs first (PowerShell): `$env:NEXT_TURBOPACK_EXPERIMENTAL_USE_SYSTEM_TLS_CERTS=1`.

**Deploying frontend changes:** build, then mirror `frontend/out/` into `backend/static/` (`robocopy frontend\out backend\static /MIR`). docker-compose bind-mounts `./backend`, so the running container serves the new files immediately — just hard-refresh the browser (Ctrl+Shift+R). The Dockerfile also bakes `backend/static` in at image build time.

Backend tests — there is no local Python (only Microsoft Store stubs) and no `uv`/`pip`, so run pytest in a throwaway container:
```
docker run --rm -v "${PWD}/backend:/app" -w /app python:3.12-slim bash -lc "pip install -q -e '.[dev]' && pytest -o addopts='-q'"
```
Tests are in `backend/app/tests/` (`pyproject.toml` `testpaths` points there).

## Conventions (from root AGENTS.md)

- Use current library versions and idiomatic patterns.
- Keep it simple. No over-engineering, no defensive code for cases that can't occur, no unrequested features.
- Be concise; keep docs minimal. **No emojis anywhere.**
- Diagnose root cause with evidence before fixing. Don't guess-and-retry.
- Colors: accent yellow `#ecad0a`, primary blue `#209dd7`, secondary purple `#753991`, dark navy `#032147`, gray text `#888888`.

## Environment

`.env` (gitignored; `.env.example` tracked) is loaded by `app/config.py` via python-dotenv; in Docker the values come from compose `env_file`. Keys:
- `OPENROUTER_API_KEY` — **a real OpenRouter key is required for the AI endpoints**; `/api/ai/test` and `/api/ai/chat` return 500 with a placeholder key.
- `SECRET_KEY` — JWT signing secret (read by `config.py`; aligned with `.env.example`).
- `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL` — optional overrides (default `openai/gpt-oss-120b`).
- `DATABASE_URL`, `DEBUG` — present in `.env`; the SQLite path is currently hardcoded in `database.py` to `backend/data/app.db`.
