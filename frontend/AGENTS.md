# Frontend Architecture & Codebase Guide

> **Note.** This guide describes the intended design. The app is now wired to the
> backend via `src/lib/api.ts` (board load/persist, optimistic updates) and ships
> an `AIChatSidebar`, card editing, and ←/→ card moves. Component prop lists below
> may be out of date; for current, verified behavior see `CLAUDE.md` and `src/`.

## Overview

**Kanban Studio** is a Next.js 16+ frontend for a collaborative Kanban board. Currently a demo with client-side state only; will integrate with backend API in Part 7.

- **Framework:** Next.js 16.1.6, React 19.2.3, TypeScript
- **Styling:** Tailwind CSS 4 with PostCSS
- **Testing:** Vitest (unit) + Playwright (E2E)
- **Drag & Drop:** @dnd-kit (core, sortable, utilities)

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx           # Root page, exports <KanbanBoard />
│   │   ├── layout.tsx         # HTML layout wrapper, metadata, global styles
│   │   └── globals.css        # Global styles, Tailwind imports
│   ├── components/
│   │   ├── KanbanBoard.tsx    # Main drag-drop controller, state manager
│   │   ├── KanbanColumn.tsx   # Column wrapper, rename handler
│   │   ├── KanbanCard.tsx     # Card component, edit handler
│   │   ├── KanbanCardPreview.tsx # Overlay preview during drag
│   │   ├── NewCardForm.tsx    # Form to create new card
│   │   ├── KanbanBoard.test.tsx
│   │   └── KanbanCard.test.tsx
│   ├── lib/
│   │   ├── kanban.ts          # Core types, initialData, moveCard logic
│   │   └── kanban.test.ts     # Unit tests for kanban utilities
│   └── test/
│       ├── setup.ts           # Vitest setup, mocks
│       └── vitest.d.ts        # Vitest type definitions
├── tests/
│   └── kanban.spec.ts         # Playwright E2E tests
├── package.json
├── tsconfig.json
├── next.config.ts
├── tailwind.config.ts
├── postcss.config.mjs
├── vitest.config.ts
├── playwright.config.ts
├── eslint.config.mjs
└── README.md

public/                         # Static assets (favicon, icons, etc.)
```

## Key Components

### KanbanBoard.tsx
**Purpose:** Main state container, drag-drop orchestration.

**State:**
- `board: BoardData` - full board structure (columns + cards)
- `activeCardId: string | null` - dragging card reference

**Key Methods:**
- `handleDragStart()` - sets active card for overlay preview
- `handleDragEnd()` - calls `moveCard()` to update state
- `handleRenameColumn()` - updates column title
- `handleAddCard()` - creates new card in column
- `handleEditCard()` - updates card title/details
- `handleDeleteCard()` - removes card from board

**Styling:** Uses Tailwind grid layout for columns.

### KanbanColumn.tsx
**Purpose:** Renders single column with droppable area + cards list.

**Props:**
- `column: Column` - column data
- `cards: Record<string, Card>` - all cards (hydration)
- `onRename: (title: string) => void`
- `onAddCard: (title: string, details: string) => void`
- `onEditCard: (cardId: string, title: string, details: string) => void`
- `onDeleteCard: (cardId: string) => void`

**Children:** Renders `<KanbanCard>` for each card in column's `cardIds`.

### KanbanCard.tsx
**Purpose:** Individual card with edit/delete UI.

**Props:**
- `card: Card`
- `onEdit: (title: string, details: string) => void`
- `onDelete: () => void`

**Features:**
- Hover state shows edit/delete buttons
- Click to edit toggles modal or inline edit
- Draggable via @dnd-kit

### KanbanCardPreview.tsx
**Purpose:** Overlay preview during drag (shows card being dragged).

**Props:**
- `card: Card | undefined`

**Styling:** Semi-transparent overlay with card content.

### NewCardForm.tsx
**Purpose:** Form component for creating new cards.

**Props:**
- `onSubmit: (title: string, details: string) => void`
- `onCancel: () => void`

**Validation:** Title required, trim whitespace.

## Core Types & Logic (kanban.ts)

### Types
```typescript
type Card = { id: string; title: string; details: string };
type Column = { id: string; title: string; cardIds: string[] };
type BoardData = { columns: Column[]; cards: Record<string, Card> };
```

### Key Functions
- `initialData: BoardData` - 5 columns with 8 demo cards
- `createId(): string` - generates UUID for new cards
- `moveCard(columns, activeId, overId): Column[]` - card movement logic
  - Finds source & target columns
  - Removes card from source `cardIds`
  - Inserts into target `cardIds` at correct index
  - Returns new columns array

### Invariants
- `cardIds` arrays are ordered (order represents position in column)
- Every card ID in `columns[].cardIds` must exist in `cards` object
- No card can be in multiple columns

## Testing

### Unit Tests (Vitest)
- **kanban.test.ts:** `moveCard()` logic, edge cases (same column, invalid IDs, etc.)
- **KanbanBoard.test.tsx:** State updates, callback handlers
- **KanbanCard.test.tsx:** Edit/delete button visibility, form validation

**Run:** `npm run test:unit` or `npm run test:unit:watch`

### E2E Tests (Playwright)
- **kanban.spec.ts:** Full user flows
  - Drag card from Backlog to In Progress
  - Rename column
  - Create new card
  - Edit card details
  - Delete card
  - Verify card order persists after multiple drags

**Run:** `npm run test:e2e`

**Current Coverage Target:** ≥80% for components

## Color Scheme (from AGENTS.md)
- Accent Yellow: `#ecad0a` - highlights, active states
- Blue Primary: `#209dd7` - links, active columns
- Purple Secondary: `#753991` - delete buttons, danger states
- Dark Navy: `#032147` - headings, text
- Gray Text: `#888888` - labels, supporting text

## Build & Deployment

### Development
```bash
npm install
npm run dev      # Next.js dev server on localhost:3000
```

### Production Build
```bash
npm run build    # Generates .next/ with static export
```

Output: `frontend/.next/static/` → copied to `backend/static/` for FastAPI serving.

### Scripts
- `npm run lint` - ESLint check
- `npm run test` - Unit + E2E tests
- `npm run test:all` - Run all test suites with coverage

## Future Integration (Post-Part 7)

### API Client
New file: `src/lib/api.ts` will export:
- `fetchKanban(): Promise<BoardData>` - GET `/api/kanban`
- `updateCard(id, updates): Promise<Card>` - PATCH `/api/cards/{id}`
- `createCard(columnId, title, details): Promise<Card>` - POST `/api/cards`
- `deleteCard(id): Promise<void>` - DELETE `/api/cards/{id}`
- `renameColumn(id, title): Promise<Column>` - PATCH `/api/columns/{id}`

### State Management
- Replace local `useState` with React Context or Zustand
- Add loading/error states during API calls
- Implement optimistic updates with rollback on failure
- Add sync reconciliation for concurrent updates

### Authentication
- Add `<LoginForm>` component for hardcoded "user"/"password"
- Store JWT/session token in localStorage
- Redirect unauthenticated users to `/login`
- Add logout button to Kanban header

### AI Chat Sidebar
- New component: `<AIChatSidebar>` with message history + input
- New hook: `useAIChat()` for `/api/ai/chat` integration
- Real-time Kanban updates when AI mutates board

## Dependencies & Versions
- Next.js 16.1.6 - Framework
- React 19.2.3 - UI library
- Tailwind CSS 4 - Styling
- @dnd-kit 6+ - Drag & drop
- Vitest 3.2.4 - Unit tests
- Playwright 1.58.0 - E2E tests
- TypeScript 5 - Type safety
- ESLint 9 - Linting

All at latest stable versions as of May 2026.
