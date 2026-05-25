# Database Schema & Design

> **Implementation note.** The DDL below is the original design. The shipped
> models (`backend/app/models.py`) use table names `kanban_columns` and
> `kanban_cards` (not `columns`/`cards`), the column/card ordering field is
> `position` (not `order`), and column/card labels use `title` (cards also have
> `description`). Tables are created from the ORM models via
> `Base.metadata.create_all`; the explicit FK/UNIQUE constraints shown here are
> not all declared on the models. Treat `models.py` as the source of truth.

## Overview

The database is built with SQLite + SQLAlchemy ORM for MVP simplicity and portability. Schema auto-creates on first run. Designed for single user per session (MVP limitation) with future multi-user support.

## Physical Schema (SQLite DDL)

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Kanban boards table (one per user for MVP)
CREATE TABLE kanban_boards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL DEFAULT 'My Board',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Columns table (5 fixed columns per board)
CREATE TABLE columns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    "order" INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (board_id) REFERENCES kanban_boards(id) ON DELETE CASCADE,
    UNIQUE(board_id, "order")
);

-- Cards table
CREATE TABLE cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    column_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    "order" INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE,
    UNIQUE(column_id, "order")
);

-- Conversation history (Part 9)
CREATE TABLE ai_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    board_id INTEGER NOT NULL,
    role VARCHAR(10) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (board_id) REFERENCES kanban_boards(id) ON DELETE CASCADE
);
```

## Logical Model (Entities & Relationships)

### User
- **Role:** Identity and authentication
- **Attributes:**
  - `id` (PK): Unique identifier
  - `username` (UNIQUE): Credentials
  - `password_hash`: Bcrypt/Argon2 hash
  - `created_at`: Account creation timestamp

### KanbanBoard
- **Role:** Container for a user's project
- **Attributes:**
  - `id` (PK): Unique identifier
  - `user_id` (FK, UNIQUE): One board per user (MVP)
  - `name`: Board title (editable)
  - `created_at`: Creation timestamp
- **Relationships:**
  - Has many `Column` (1:N)
  - Belongs to `User` (N:1)

### Column
- **Role:** Fixed swimlane in Kanban (e.g., "Backlog", "In Progress")
- **Attributes:**
  - `id` (PK): Unique identifier
  - `board_id` (FK): Parent board
  - `name`: Column title (editable, default: "Backlog", "Discovery", "In Progress", "Review", "Done")
  - `order` (UNIQUE per board): Display position (0-4 for MVP)
  - `created_at`: Creation timestamp
- **Relationships:**
  - Has many `Card` (1:N)
  - Belongs to `KanbanBoard` (N:1)
- **Constraints:**
  - Max 5 columns per board (fixed for MVP)
  - Order must be sequential and unique within board

### Card
- **Role:** Task/work item on the board
- **Attributes:**
  - `id` (PK): Unique identifier
  - `column_id` (FK): Current column location
  - `title` (NOT NULL): Card title
  - `description`: Long-form details
  - `order`: Position in column (0 = topmost)
  - `created_at`: Creation timestamp
  - `updated_at`: Last modification timestamp
- **Relationships:**
  - Belongs to `Column` (N:1)
  - Can be mutated by `AIMessage` (1:N, implicit)
- **Constraints:**
  - Title required, max 255 chars
  - Description optional, unlimited length
  - Order unique per column
  - No card can be in two columns simultaneously

### AIMessage (Part 9)
- **Role:** Conversation history for AI chat
- **Attributes:**
  - `id` (PK): Message identifier
  - `board_id` (FK): Conversation context
  - `role`: "user" or "assistant"
  - `content`: Message text
  - `created_at`: Timestamp
- **Relationships:**
  - Belongs to `KanbanBoard` (N:1)
- **Notes:**
  - Stored server-side for context in subsequent AI calls
  - Populated by `/api/ai/chat` endpoint

## Logical JSON View (Frontend API Response)

The `/api/kanban` endpoint returns:

```json
{
  "columns": [
    {
      "id": 1,
      "name": "Backlog",
      "order": 0
    },
    {
      "id": 2,
      "name": "Discovery",
      "order": 1
    },
    ...
  ],
  "cards": [
    {
      "id": 101,
      "column_id": 1,
      "title": "Align roadmap themes",
      "description": "Draft quarterly themes with impact statements and metrics.",
      "order": 0
    },
    {
      "id": 102,
      "column_id": 1,
      "title": "Gather customer signals",
      "description": "Review support tags, sales notes, and churn feedback.",
      "order": 1
    },
    ...
  ]
}
```

**Note:** Mirrors frontend's internal `BoardData` type for easy round-trip serialization.

## Data Integrity & Constraints

### Primary Keys
- All tables use auto-increment integer PKs for performance and simplicity

### Foreign Keys
- All FKs have `ON DELETE CASCADE` for referential integrity
- Deleting user → board + columns + cards deleted
- Deleting column → cards deleted

### Unique Constraints
- `users.username`: Only one user per login credential
- `kanban_boards.user_id`: One board per user (MVP)
- `columns.board_id, order`: One column per board at each position
- `cards.column_id, order`: One card per column at each position

### Not Null Constraints
- `users.username`, `password_hash`
- `kanban_boards.user_id`, `name`
- `columns.board_id`, `name`, `order`
- `cards.column_id`, `title`, `order`, `created_at`

## Indexes

**Current (auto-indexed by SQLite):**
- PKs and UNIQUEs have indexes
- FKs should be indexed for join performance

**Recommended (post-MVP):**
- `cards.column_id` - for column → cards queries
- `ai_messages.board_id` - for conversation history lookups
- `ai_messages.created_at` - for time-ordered queries

## Migration Strategy

**For MVP:** SQLAlchemy `Base.metadata.create_all()` auto-creates schema on startup.

```python
# In app/database.py
def init_db():
    Base.metadata.create_all(bind=engine)

# In app/main.py startup
@app.on_event("startup")
async def startup():
    init_db()
```

**For production (post-MVP):** Migrate to Alembic for versioned migrations.

## Scalability Notes

**Current Design Limitations:**
- SQLite is single-writer (acceptable for MVP; use PostgreSQL post-MVP)
- No sharding or partitioning (single user per session)
- AI conversation history stored inline (could move to separate service)

**Future Enhancements:**
- Migrate to PostgreSQL for concurrent users
- Add indexes on frequently-queried columns
- Consider document storage (MongoDB) for flexible card metadata
- Archive old conversations to reduce DB size
- Add full-text search on card titles/descriptions

## Example Data Flow

1. **User signs in:**
   - Auth service creates JWT
   - Frontend stores token
2. **GET /api/kanban:**
   - Backend queries `kanban_boards` for user
   - Queries `columns` and `cards` for that board
   - Returns JSON
3. **Create card:**
   - Frontend POSTs `{ column_id, title, description }`
   - Backend inserts into `cards` with `order = max_order + 1`
   - Returns new card JSON
4. **Move card between columns:**
   - Frontend identifies source/target columns
   - Backend updates `cards.column_id` and reorders `order` in each column
5. **AI chat:**
   - Frontend POSTs message + conversation history
   - Backend inserts message into `ai_messages` (role=user)
   - Calls OpenRouter with full Kanban context
   - Inserts AI response into `ai_messages` (role=assistant)
   - Applies mutations to `cards`/`columns` if provided
   - Returns response + updated board to frontend

## Backup & Recovery

**For MVP:** Backup `backend/data/app.db` file.

**Recommended Strategy:**
- Daily automated backups to cloud storage
- Point-in-time recovery capability
- WAL (Write-Ahead Logging) mode for durability

```python
# In app/database.py
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "journal_mode": "WAL"}
)
```
