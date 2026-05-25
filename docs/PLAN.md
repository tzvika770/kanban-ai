# Project Management MVP - Detailed Execution Plan

> **Status: all parts implemented.** Parts 4-10 (auth wiring, DB-backed CRUD,
> frontend/backend integration, AI connectivity and chat sidebar) are complete
> and verified end-to-end against a real OpenRouter key. The per-part checklists
> below are the original plan and may use names that differ from the shipped
> code; `backend/app/` and `CLAUDE.md` are authoritative for current behavior.

## Architecture Decisions

**Backend Structure:**
- `backend/app/main.py` - FastAPI entry point with CORS, static file serving
- `backend/app/models.py` - SQLAlchemy ORM models (User, KanbanBoard, Card, Column)
- `backend/app/database.py` - SQLite connection, session management, auto-migration
- `backend/app/routes/` - API endpoints (auth, kanban CRUD, AI)
- `backend/app/schemas.py` - Pydantic models for request/response validation
- `backend/app/ai.py` - OpenRouter integration with structured outputs
- `backend/pyproject.toml` - uv-based package management
- `backend/data/app.db` - SQLite database (auto-created on first run)

**Frontend Build:**
- Next.js static export → `backend/static/`
- Frontend served by FastAPI at `/`

**Environment:**
- `.env.example` tracked; `.env` gitignored
- Contains: `OPENROUTER_API_KEY`, database path, debug flags

---

## Part 1: Planning & Architecture Documentation

**Goals:** Enrich plan with detailed checklists, acceptance criteria, tests. Document frontend & backend architecture.

### Subtasks:
- [ ] Enrich docs/PLAN.md with detailed phases, checklists, success criteria (THIS FILE)
- [ ] Create frontend/AGENTS.md describing existing frontend code, components, test structure
- [ ] Create backend/AGENTS.md describing backend architecture, API contract, DB schema proposal
- [ ] Create docs/DATABASE_SCHEMA.md with proposed SQLite schema (JSON view + SQL DDL)
- [ ] Create docs/API_SPEC.md with all backend endpoints, request/response formats
- [ ] Review and get user sign-off on all documentation

### Success Criteria:
- ✓ All 5 architectural docs created and reviewed
- ✓ User confirms they understand the architecture
- ✓ No ambiguity about backend structure, API endpoints, or database design

---

## Part 2: Scaffolding & Docker Setup ✅ COMPLETED

**Goals:** Set up Docker infrastructure, minimal FastAPI backend, start/stop scripts with "hello world" verification.

### Subtasks:
- [x] Create Dockerfile (Python 3.12+, pip-based)
- [x] Create docker-compose.yml for local development
- [x] Create `backend/pyproject.toml` with FastAPI, SQLAlchemy, python-dotenv, openai, etc.
- [x] Create `backend/app/main.py` with FastAPI app, health check endpoint `/api/health`, CORS setup
- [x] Create `backend/app/database.py` with SQLite connection, session factory
- [x] Create `.env.example` with `OPENROUTER_API_KEY=`, database defaults
- [x] Create `scripts/start.sh`, `scripts/start.bat`, `scripts/start.ps1` (Mac/Linux/Windows)
- [x] Create `scripts/stop.sh`, `scripts/stop.bat`, `scripts/stop.ps1`
- [x] Test Docker build and run locally; verify `/api/health` returns 200

### Success Criteria:
- ✅ Docker builds without errors
- ✅ `docker-compose up` runs successfully
- ✅ HTTP GET `/api/health` returns `{"status": "ok", "service": "pm-backend", "version": "0.1.0"}`
- ✅ Start/stop scripts work on Windows (tested)
- ✅ SQLite database auto-created at `backend/data/app.db`
- ✅ Container health check passing

### Completion Notes:
- **Docker image:** `pm-backend` built and running on port 8000
- **Database:** SQLite initialized, app.db auto-created on startup
- **Health endpoint:** `/api/health` returns 200 OK with JSON
- **Start/stop scripts:** All three versions (sh/bat/ps1) created and functional
- **Environment:** .env configured with test API key for local testing

---

## Part 3: Frontend Integration & Static Build ✅ COMPLETED

**Goals:** Build Next.js frontend statically, serve from FastAPI, verify Kanban board displays at `/`.

### Subtasks:
- [x] Update `frontend/next.config.ts` to enable static export
- [x] Update FastAPI `app/main.py` to serve static files from `backend/static/` at `/`
- [x] Build frontend with `npm run build` to generate `frontend/out/`
- [x] Copy frontend build to `backend/static/` 
- [x] Rebuild Docker image with static files included
- [x] Verify `http://localhost:8000/` loads the Kanban board UI
- [ ] Add frontend unit tests (Vitest) for all components—verify 80%+ coverage
- [ ] Add E2E tests (Playwright) for core flows: drag/drop, edit card, add card

### Success Criteria:
- ✅ `http://localhost:8000/` shows Kanban board
- ✅ HTML content served with React components
- ✅ Frontend static files in backend/static/
- ✅ Docker image includes frontend build
- ⏳ All existing frontend tests pass (ready for next phase)
- ⏳ E2E tests verify drag/drop, card editing, card creation work

### Completion Notes:
- **Frontend build:** Next.js static export working, output in frontend/out/
- **Static serving:** FastAPI StaticFiles middleware serving at /
- **Docker:** Image rebuilt with frontend assets, running successfully
- **Kanban board:** Accessible at http://localhost:8000/, all elements present
- **Bundle size:** Optimized production build with Turbopack

---

## Part 4: User Authentication (Hardcoded Credentials)

**Goals:** Add login/logout flow with hardcoded credentials ("user"/"password"). Only authenticated users see the Kanban.

### Subtasks:
- [ ] Create `/api/auth/login` endpoint (POST username/password → JWT or session token)
- [ ] Create `/api/auth/logout` endpoint (clears session/token)
- [ ] Add JWT middleware to protect `/api/kanban/*` routes
- [ ] Create `backend/app/auth.py` with credential validation, token generation
- [ ] Update frontend to show login form at `/` if not authenticated
- [ ] Add login/logout buttons and session state management (React Context or similar)
- [ ] Add E2E tests for login flow: fail with wrong credentials, succeed with correct, logout clears
- [ ] Add E2E test that verifies `/api/kanban` returns 401 if not authenticated

### Success Criteria:
- ✓ Unauthenticated requests to `/api/kanban/*` return 401
- ✓ Login with "user"/"password" succeeds; other credentials fail
- ✓ Frontend redirects to login if no token
- ✓ Logout clears session; next request requires re-login
- ✓ E2E tests verify full auth flow

---

## Part 5: Database Schema & Data Model

**Goals:** Design and document database schema. Get user approval.

### Subtasks:
- [ ] Design SQLAlchemy models in `backend/app/models.py`:
  - `User` (id, username, created_at)
  - `KanbanBoard` (id, user_id, name, created_at)
  - `Column` (id, board_id, name, order, created_at)
  - `Card` (id, column_id, title, description, order, created_at, updated_at)
- [ ] Export schema as JSON in `docs/DATABASE_SCHEMA.json`
- [ ] Create `docs/DATABASE_DESIGN.md` explaining schema, relationships, indexes
- [ ] Create migration/DDL script `backend/app/migrations.py` (SQLAlchemy creates tables on first run)
- [ ] Write unit tests for model relationships and constraints
- [ ] Get user sign-off on schema

### Success Criteria:
- ✓ `docs/DATABASE_SCHEMA.json` accurately represents models
- ✓ `docs/DATABASE_DESIGN.md` explains relationships and design decisions
- ✓ User reviews and approves schema
- ✓ Unit tests validate model constraints and relationships

---

## Part 6: Backend API Routes & Database Integration

**Goals:** Implement full CRUD API for Kanban. Database auto-creates on first run. Comprehensive backend unit tests.

### Subtasks:
- [ ] Implement API endpoints in `backend/app/routes/`:
  - `GET /api/kanban` → list user's columns and cards
  - `POST /api/cards` → create new card
  - `PATCH /api/cards/{card_id}` → update card (title, description, column_id, order)
  - `DELETE /api/cards/{card_id}` → delete card
  - `PATCH /api/columns/{column_id}` → rename column
  - `PATCH /api/columns/{column_id}/order` → reorder cards in column
- [ ] Implement SQLAlchemy session management with dependency injection
- [ ] Create `backend/app/database.py` that auto-initializes DB schema on first run
- [ ] Add request validation (Pydantic schemas)
- [ ] Add error handling and logging
- [ ] Write comprehensive backend unit tests (pytest) for each endpoint:
  - Happy paths (200, 201 responses)
  - Error cases (400, 401, 404, 500)
  - Edge cases (empty lists, invalid IDs, concurrent updates)
- [ ] Aim for ≥ 85% backend test coverage

### Success Criteria:
- ✓ All CRUD endpoints work correctly via HTTP
- ✓ Database auto-creates on first run; schema matches `DATABASE_SCHEMA.json`
- ✓ Authentication required for all `/api/kanban/*` endpoints
- ✓ Backend unit tests ≥ 85% coverage, all passing
- ✓ Error responses include descriptive messages and appropriate status codes

---

## Part 7: Frontend ↔ Backend Integration

**Goals:** Connect frontend to backend API. Persistent Kanban across sessions. Full integration tests.

### Subtasks:
- [ ] Create API client module `frontend/src/lib/api.ts` with fetch-based methods for all endpoints
- [ ] Update frontend state management to fetch from `/api/kanban` on load
- [ ] Implement optimistic UI updates + server-side reconciliation for drag/drop
- [ ] Update card creation, editing, deletion to call backend APIs
- [ ] Add error handling and retry logic for failed requests
- [ ] Add loading states and spinners during API calls
- [ ] Add E2E tests verifying:
  - Kanban persists after page reload
  - Drag/drop syncs to backend
  - Card edits are saved and visible after reload
  - Concurrent updates don't cause data loss
- [ ] Add integration tests for frontend-backend interaction (mocked API server)

### Success Criteria:
- ✓ Kanban data persists across page reloads
- ✓ All UI interactions (drag, edit, create, delete) sync with backend
- ✓ Error handling prevents data corruption on failed requests
- ✓ E2E tests verify persistence and sync
- ✓ No data loss in concurrent scenarios

---

## Part 8: AI Connectivity & Structured Outputs Setup

**Goals:** Verify OpenRouter API works. Test with simple prompt. Set up structured output schema.

### Subtasks:
- [ ] Create `backend/app/ai.py` with OpenRouter client initialization
- [ ] Add `POST /api/ai/test` endpoint that calls OpenRouter with "2+2?" and returns response
- [ ] Add `.env.example` with `OPENROUTER_API_KEY` placeholder
- [ ] Test manually: `curl -X POST http://localhost:8000/api/ai/test`
- [ ] Design Pydantic model for AI structured output (response text + optional Kanban mutations)
- [ ] Add unit tests for AI client (mock OpenRouter API)
- [ ] Add integration test that verifies AI endpoint works with real API (use test key)

### Success Criteria:
- ✓ `/api/ai/test` returns correct response to "2+2?"
- ✓ Structured output schema defined and validated
- ✓ AI unit tests mock API; integration tests use real API with test credentials
- ✓ Error handling for API rate limits, auth failures, network issues

---

## Part 9: AI Kanban Mutations with Structured Outputs

**Goals:** AI receives full Kanban state + user question. Returns response + optional mutations. Full test coverage.

### Subtasks:
- [ ] Create `POST /api/ai/chat` endpoint that:
  - Accepts user message + conversation history
  - Sends full Kanban JSON to OpenRouter with user message
  - Uses structured output schema (response + mutations)
  - Applies mutations to Kanban if provided
  - Returns response + updated Kanban to frontend
- [ ] Define mutation types: `CreateCard`, `UpdateCard`, `DeleteCard`, `MoveCard`, `RenameColumn`
- [ ] Implement mutation application logic with validation
- [ ] Add retry logic for transient OpenRouter failures
- [ ] Write comprehensive tests:
  - Unit tests for mutation logic (valid and invalid mutations)
  - Integration tests for full flow: user message → AI response → Kanban updated
  - Test edge cases: concurrent AI calls, failed mutations, rate limits
- [ ] Aim for ≥ 80% coverage on AI logic

### Success Criteria:
- ✓ AI receives full Kanban context in each request
- ✓ Structured output schema correctly parsed and validated
- ✓ Mutations applied atomically; failed mutations rollback
- ✓ Tests cover happy paths, errors, edge cases
- ✓ Conversation history maintained server-side

---

## Part 10: AI Chat Sidebar & Real-Time UI Updates

**Goals:** Beautiful sidebar chat widget. AI can update Kanban; UI refreshes automatically.

### Subtasks:
- [ ] Create `frontend/src/components/AIChatSidebar.tsx` with:
  - Message display area (user + AI messages)
  - Input field for user questions
  - Loading indicator during AI processing
- [ ] Integrate with `/api/ai/chat` endpoint
- [ ] Implement automatic UI refresh when AI mutates Kanban:
  - Fetch updated Kanban or receive mutations in response
  - Update React state to trigger re-render
  - Smooth animations for card movements, creations, deletions
- [ ] Add conversation persistence (load history from backend on page load)
- [ ] Add E2E tests verifying:
  - Chat message sends and receives response
  - AI-driven mutations appear in Kanban immediately
  - Multiple mutations in one response all apply
- [ ] Apply color scheme: accent yellow (#ecad0a), blue (#209dd7), purple (#753991)
- [ ] Mobile-responsive layout

### Success Criteria:
- ✓ Chat sidebar is functional and responsive
- ✓ AI responses and Kanban mutations appear in real-time
- ✓ Conversation history persists across sessions
- ✓ All color scheme guidelines applied
- ✓ E2E tests verify AI chat + Kanban update flow
- ✓ No UI flicker or data inconsistency