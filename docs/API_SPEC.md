# API Specification

> **Implementation note.** This spec is the original design. The shipped API
> (`backend/app/schemas.py`, `backend/app/routes/`) differs in a few names:
> columns/cards use `title` and `position` rather than `name` and `order`; the
> kanban response is `{columns, cards}` without a `data`/`status` envelope; and
> the login response returns `{access_token, token_type, username}`. The AI chat
> response is `{response, mutations, updated_board}`. Treat `schemas.py` as the
> source of truth.

## Base URL
```
http://localhost:8000/api
```

## Authentication

All endpoints under `/api/kanban/*` and `/api/ai/*` require JWT token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after 24 hours. Expired requests return `401 Unauthorized`.

## Response Format

All responses are JSON.

### Success Response (2xx)
```json
{
  "data": {},
  "status": "success"
}
```
Or directly the resource (cards, columns, etc.) for CRUD operations.

### Error Response (4xx, 5xx)
```json
{
  "detail": "Human-readable error message",
  "error_code": "ERROR_TYPE",
  "timestamp": "2026-05-24T10:30:00Z"
}
```

## Endpoints

---

## Authentication Routes

### Login
**POST** `/auth/login`

Authenticate with hardcoded credentials.

**Request:**
```json
{
  "username": "user",
  "password": "password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors:**
- `400 Bad Request` - Missing username or password
- `401 Unauthorized` - Invalid credentials

---

### Logout
**POST** `/auth/logout`

Invalidate current session (clears server-side token cache).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "status": "ok",
  "message": "Logged out successfully"
}
```

**Errors:**
- `401 Unauthorized` - Invalid or missing token

---

## Health Check

### Health
**GET** `/health`

Check API and database connectivity (no auth required).

**Response (200):**
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-05-24T10:30:00Z"
}
```

---

## Kanban Routes

All routes require `Authorization: Bearer <token>` header.

### Get Kanban Board
**GET** `/kanban`

Fetch the user's board with all columns and cards.

**Response (200):**
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
    {
      "id": 3,
      "name": "In Progress",
      "order": 2
    },
    {
      "id": 4,
      "name": "Review",
      "order": 3
    },
    {
      "id": 5,
      "name": "Done",
      "order": 4
    }
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
    }
  ]
}
```

**Errors:**
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Database error

---

### Create Card
**POST** `/cards`

Create a new card in a column.

**Request:**
```json
{
  "column_id": 1,
  "title": "New task",
  "description": "Task details"
}
```

**Response (201):**
```json
{
  "id": 103,
  "column_id": 1,
  "title": "New task",
  "description": "Task details",
  "order": 2,
  "created_at": "2026-05-24T10:30:00Z",
  "updated_at": "2026-05-24T10:30:00Z"
}
```

**Errors:**
- `400 Bad Request` - Missing title or invalid column_id
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Column does not exist
- `403 Forbidden` - Card is for another user's board

---

### Update Card
**PATCH** `/cards/{card_id}`

Update card title, description, column, or order.

**Request (all fields optional):**
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "column_id": 2,
  "order": 0
}
```

**Response (200):**
```json
{
  "id": 103,
  "column_id": 2,
  "title": "Updated title",
  "description": "Updated description",
  "order": 0,
  "created_at": "2026-05-24T10:30:00Z",
  "updated_at": "2026-05-24T10:30:01Z"
}
```

**Errors:**
- `400 Bad Request` - Invalid column_id or order
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Card does not exist
- `403 Forbidden` - Card is for another user's board

---

### Delete Card
**DELETE** `/cards/{card_id}`

Permanently delete a card.

**Response (200):**
```json
{
  "status": "ok",
  "message": "Card deleted successfully",
  "id": 103
}
```

**Errors:**
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Card does not exist
- `403 Forbidden` - Card is for another user's board

---

### Rename Column
**PATCH** `/columns/{column_id}`

Rename a column (columns are fixed, but names can be customized).

**Request:**
```json
{
  "name": "Todo"
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Todo",
  "order": 0
}
```

**Errors:**
- `400 Bad Request` - Name is empty
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Column does not exist
- `403 Forbidden` - Column is for another user's board

---

## AI Routes

All routes require `Authorization: Bearer <token>` header.

### AI Test
**POST** `/ai/test`

Simple connectivity test (returns "4" for "2+2").

**Response (200):**
```json
{
  "response": "4"
}
```

**Errors:**
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - OpenRouter API error

---

### AI Chat
**POST** `/ai/chat`

Send a message to AI with Kanban context. AI can respond with mutations to the board.

**Request:**
```json
{
  "message": "Create a card for user testing",
  "history": [
    {
      "role": "user",
      "content": "What should I work on next?"
    },
    {
      "role": "assistant",
      "content": "I recommend prioritizing the analytics view."
    }
  ]
}
```

**Response (200):**
```json
{
  "response": "I've created a new card for user testing in the Backlog column.",
  "mutations": [
    {
      "type": "create_card",
      "column_id": 1,
      "title": "User testing for analytics",
      "description": "Test the analytics view with real users"
    }
  ],
  "updated_board": {
    "columns": [...],
    "cards": [...]
  }
}
```

**Mutation Types:**

- `create_card`: Create new card
  ```json
  {
    "type": "create_card",
    "column_id": 1,
    "title": "Card title",
    "description": "Optional description"
  }
  ```

- `update_card`: Update card fields
  ```json
  {
    "type": "update_card",
    "card_id": 101,
    "title": "New title",
    "description": "New description"
  }
  ```

- `delete_card`: Delete card
  ```json
  {
    "type": "delete_card",
    "card_id": 101
  }
  ```

- `move_card`: Move card to column (order auto-adjusted)
  ```json
  {
    "type": "move_card",
    "card_id": 101,
    "column_id": 3,
    "order": 0
  }
  ```

- `rename_column`: Rename column
  ```json
  {
    "type": "rename_column",
    "column_id": 1,
    "name": "New column name"
  }
  ```

**Errors:**
- `400 Bad Request` - Message is empty
- `401 Unauthorized` - Missing or invalid token
- `422 Unprocessable Entity` - Mutation schema validation failed
- `500 Internal Server Error` - OpenRouter API error or mutation application failed

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Username/password incorrect |
| `INVALID_TOKEN` | 401 | Token missing, expired, or invalid |
| `UNAUTHORIZED` | 403 | User doesn't have permission to access resource |
| `NOT_FOUND` | 404 | Resource (card, column, board) doesn't exist |
| `VALIDATION_ERROR` | 400 | Request body failed validation |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `AI_ERROR` | 500 | OpenRouter API error |
| `MUTATION_FAILED` | 422 | Card/column mutation validation failed |

---

## Rate Limiting (Future)

Currently no rate limiting. Post-MVP considerations:
- Limit to 100 requests per minute per user
- Limit AI chat to 10 calls per minute (expensive)

---

## Versioning (Future)

Currently at v1 (implicit). Future versions might include:
- `/api/v2/` endpoints
- Backward compatibility maintained for old clients

---

## Example Workflows

### 1. Login → Fetch Board → Create Card
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Response: {"access_token": "eyJh..."}

# Fetch board
curl -X GET http://localhost:8000/api/kanban \
  -H "Authorization: Bearer eyJh..."

# Create card
curl -X POST http://localhost:8000/api/cards \
  -H "Authorization: Bearer eyJh..." \
  -H "Content-Type: application/json" \
  -d '{
    "column_id": 1,
    "title": "New task",
    "description": "Details"
  }'
```

### 2. AI Chat with Mutation
```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Authorization: Bearer eyJh..." \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Move all discovery tasks to in progress",
    "history": []
  }'

# Response: mutation to move cards, updated_board with new state
```

---

## CORS & Preflight

CORS is enabled for local development (all origins).

**Preflight Request:**
```
OPTIONS /api/kanban
Access-Control-Request-Method: GET
```

**Response Headers:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## Testing

See `backend/app/tests/` for:
- `test_auth.py` - Authentication endpoint tests
- `test_kanban.py` - CRUD endpoint tests
- `test_ai.py` - AI chat and mutation tests

Run with:
```bash
pytest tests/ -v --cov=app
```
