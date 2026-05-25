# Backend Architecture & Implementation Guide

> **Note.** This guide describes the intended design and is largely realized,
> but some names/snippets differ from the shipped code (e.g. models use
> `KanbanColumn`/`title`/`position`, not `Column`/`name`/`order`). For current,
> verified behavior see `CLAUDE.md` and the code in `app/`.

## Overview

**Project Management Backend** is a FastAPI application serving the Kanban board API, AI integration, and authentication. Designed for simplicity, scalability, and clear separation of concerns.

- **Framework:** FastAPI 0.100+, Python 3.12+
- **Database:** SQLite with SQLAlchemy ORM
- **Package Manager:** uv (modern Python packaging)
- **AI:** OpenRouter API with structured outputs
- **Testing:** pytest with fixtures, mocking

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, static file serving, root routes
│   ├── database.py          # SQLAlchemy setup, session factory, migrations
│   ├── models.py            # SQLAlchemy ORM models (User, KanbanBoard, Column, Card)
│   ├── schemas.py           # Pydantic request/response models
│   ├── auth.py              # JWT/token logic, credential validation
│   ├── routes/
│   │   ├── auth.py          # POST /api/auth/login, /api/auth/logout
│   │   ├── kanban.py        # GET /api/kanban, CRUD /api/cards/*, /api/columns/*
│   │   └── ai.py            # POST /api/ai/test, /api/ai/chat
│   ├── ai.py                # OpenRouter client, structured output handling
│   └── tests/
│       ├── conftest.py      # pytest fixtures (db, client, auth token)
│       ├── test_auth.py     # Login, logout, token validation
│       ├── test_kanban.py   # CRUD operations, permissions, edge cases
│       ├── test_ai.py       # AI mutations, structured outputs
│       └── test_models.py   # ORM relationships, constraints
├── data/
│   └── app.db               # SQLite database (created on first run)
├── .env.example             # Template for environment variables
├── pyproject.toml           # uv dependencies, tool configs
├── Dockerfile               # Docker build config
└── README.md                # Backend setup & run instructions
```

## Architecture Decisions

### Database
- **Engine:** SQLite (local development, auto-create if missing)
- **ORM:** SQLAlchemy 2.0+ (declarative models, async-ready)
- **Migrations:** Auto-schema creation on first run (no Alembic needed for MVP)

### Authentication
- **Credentials:** Hardcoded ("user", "password") for MVP
- **Token:** JWT stored in `Authorization: Bearer <token>` header
- **Session:** Stateless; token validity checked on each request

### API Design
- **Base URL:** `http://localhost:8000/api/`
- **Response Format:** JSON with consistent error structure
- **Status Codes:** Standard HTTP (200, 201, 400, 401, 404, 500)
- **Error Handling:** Descriptive error messages, logging

### AI Integration
- **Provider:** OpenRouter (cost-effective, model flexibility)
- **Model:** `openai/gpt-oss-120b` (efficient, open-source alternative)
- **Structured Outputs:** Pydantic models enforced by OpenRouter
- **Conversation History:** Stored server-side (Part 9)

## Core Data Models

### User
```python
class User(Base):
    id: int (PK)
    username: str (unique)
    password_hash: str
    created_at: datetime
```

### KanbanBoard
```python
class KanbanBoard(Base):
    id: int (PK)
    user_id: int (FK → User)
    name: str
    created_at: datetime
```

### Column
```python
class Column(Base):
    id: int (PK)
    board_id: int (FK → KanbanBoard)
    name: str
    order: int (position in board)
    created_at: datetime
```

### Card
```python
class Card(Base):
    id: int (PK)
    column_id: int (FK → Column)
    title: str
    description: str
    order: int (position in column)
    created_at: datetime
    updated_at: datetime
```

## Pydantic Schemas (Request/Response)

### Auth Schemas
- `LoginRequest(username, password)` → `TokenResponse(access_token, token_type)`
- `LogoutRequest()` → `{"status": "ok"}`

### Kanban Schemas
- `ColumnResponse(id, name, order)`
- `CardResponse(id, title, description, column_id, order)`
- `KanbanResponse(columns: List[ColumnResponse], cards: List[CardResponse])`
- `CreateCardRequest(column_id, title, description)` → `CardResponse`
- `UpdateCardRequest(title?, description?, column_id?, order?)` → `CardResponse`
- `RenameColumnRequest(name)` → `ColumnResponse`

### AI Schemas
- `AIChatRequest(message: str, history?: List[{role, content}])`
- `AIMutation = CreateCard | UpdateCard | DeleteCard | MoveCard | RenameColumn`
- `AIChatResponse(response: str, mutations?: List[AIMutation])`

## API Endpoints

### Authentication
| Method | Endpoint | Request | Response | Auth |
|--------|----------|---------|----------|------|
| POST | `/api/auth/login` | `{username, password}` | `{access_token, token_type}` | No |
| POST | `/api/auth/logout` | - | `{status: ok}` | JWT |

### Kanban
| Method | Endpoint | Request | Response | Auth |
|--------|----------|---------|----------|------|
| GET | `/api/kanban` | - | `KanbanResponse` | JWT |
| POST | `/api/cards` | `CreateCardRequest` | `CardResponse` | JWT |
| PATCH | `/api/cards/{id}` | `UpdateCardRequest` | `CardResponse` | JWT |
| DELETE | `/api/cards/{id}` | - | `{status: ok}` | JWT |
| PATCH | `/api/columns/{id}` | `RenameColumnRequest` | `ColumnResponse` | JWT |

### AI
| Method | Endpoint | Request | Response | Auth |
|--------|----------|---------|----------|------|
| POST | `/api/ai/test` | - | `{response: "4"}` | JWT |
| POST | `/api/ai/chat` | `AIChatRequest` | `AIChatResponse` | JWT |

## Implementation Details

### main.py
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS for frontend dev
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Include routers
app.include_router(auth_routes)
app.include_router(kanban_routes)
app.include_router(ai_routes)

# Health check
@app.get("/api/health")
def health():
    return {"status": "ok"}

# Static files (after routes so /api/* takes precedence)
app.mount("/", StaticFiles(directory="static", html=True))
```

### database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:///./data/app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Dependency for FastAPI to inject DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### auth.py
```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")
ALGORITHM = "HS256"

def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, ALGORITHM)

def verify_token(token: str) -> str:
    """Raises InvalidTokenError if invalid."""
    payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
    return payload["sub"]
```

### routes/kanban.py
```python
@router.get("/api/kanban")
def get_kanban(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    board = db.query(KanbanBoard).filter_by(user_id=current_user.id).first()
    columns = db.query(Column).filter_by(board_id=board.id).order_by(Column.order).all()
    cards = db.query(Card).filter(Card.column_id.in_([c.id for c in columns])).all()
    return KanbanResponse(columns=[...], cards=[...])

@router.post("/api/cards")
def create_card(req: CreateCardRequest, db: Session = Depends(get_db)):
    card = Card(**req.dict())
    db.add(card)
    db.commit()
    return CardResponse.from_orm(card)
```

### routes/ai.py
```python
@router.post("/api/ai/chat")
def ai_chat(req: AIChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get user's kanban
    board = fetch_kanban_for_user(current_user.id, db)
    
    # Call OpenRouter with structured output
    response = ai_client.chat(
        messages=[
            {"role": "user", "content": req.message},
            # Kanban context
        ],
        response_format=AIChatResponse,  # Structured output schema
    )
    
    # Apply mutations to DB if provided
    for mutation in response.mutations or []:
        apply_mutation(mutation, current_user.id, db)
    
    return response
```

## Testing Strategy

### Unit Tests (pytest)
- **test_auth.py**
  - Login with correct credentials → token
  - Login with wrong password → 401
  - Invalid token → 401
  - Logout clears session

- **test_kanban.py**
  - GET `/api/kanban` returns user's board
  - Create card → appears in kanban
  - Move card between columns → order updates
  - Rename column → persists
  - Delete card → removed from board
  - 401 for unauthenticated requests
  - 404 for non-existent card
  - 403 for accessing other user's board

- **test_ai.py**
  - AI test endpoint returns "4" for "2+2"
  - Structured output validation
  - Mutations parsed correctly
  - Card creation via AI mutation
  - Concurrent AI calls don't corrupt data

- **test_models.py**
  - Foreign key relationships maintained
  - Cascade deletes work (delete column → cards deleted)
  - Unique constraints (username)

### Integration Tests
- End-to-end flow: login → fetch kanban → create card → AI suggests update → update applied
- Error recovery: failed AI call doesn't corrupt board state

### Coverage Target
- ≥ 85% backend code coverage

## Running Locally

### Setup
```bash
cd backend
uv venv
source venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"
```

### Development
```bash
# Initialize DB
python -m app.database

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Docker
```bash
docker build -t pm-backend .
docker run -p 8000:8000 -v $(pwd)/data:/app/data pm-backend
```

## Environment Variables

```
OPENROUTER_API_KEY=<your-key>           # Required for AI endpoints
DATABASE_URL=sqlite:///./data/app.db   # Optional, defaults to this
SECRET_KEY=<jwt-secret>                 # Optional, defaults to dev key
DEBUG=False                              # Optional logging level
```

## Dependencies (pyproject.toml)
```toml
[project]
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
    "pyjwt>=2.8.0",
    "requests>=2.31.0",
    "openai>=1.0.0",  # For OpenRouter compatibility
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",  # Async test client
]
```

## Error Handling

**All errors return JSON with structure:**
```json
{
  "detail": "Descriptive error message",
  "error_code": "INVALID_TOKEN",
  "timestamp": "2026-05-24T10:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Successful read or update
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Auth required or failed
- `403 Forbidden` - User doesn't have permission
- `404 Not Found` - Resource doesn't exist
- `500 Internal Server Error` - Unexpected error (logged)

## Next Steps (Post-Part 2)

1. **Part 3:** Configure Next.js static export, update `main.py` to serve static files
2. **Part 4:** Implement login UI, JWT middleware, auth routes
3. **Part 5:** Design + document schema, get user approval
4. **Part 6:** Implement full CRUD routes, unit tests
5. **Part 7:** Connect frontend to API, integration tests
6. **Part 8-10:** AI integration with mutations and chat UI