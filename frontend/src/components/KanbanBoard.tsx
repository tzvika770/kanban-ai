"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import { createId, initialData, moveCard, type BoardData } from "@/lib/kanban";
import {
  createCard,
  deleteCard,
  fetchBoard,
  renameColumn,
  updateCard,
} from "@/lib/api";

export const KanbanBoard = () => {
  // Start from the demo board so the UI paints immediately, then replace it
  // with the persisted board once the API responds.
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  // Re-fetch the canonical board; used after a write to reconcile state.
  const reload = () => {
    fetchBoard()
      .then(setBoard)
      .catch(() => {});
  };

  useEffect(() => {
    reload();
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board.cards, [board.cards]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    const activeId = String(active.id);
    const overId = String(over.id);
    const columns = moveCard(board.columns, activeId, overId);
    const target = columns.find((column) => column.cardIds.includes(activeId));

    setBoard((prev) => ({ ...prev, columns }));

    if (target) {
      updateCard(activeId, {
        columnId: target.id,
        position: target.cardIds.indexOf(activeId),
      }).catch(reload);
    }
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    setBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleCommitRename = (columnId: string, title: string) => {
    renameColumn(columnId, title).catch(reload);
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    setBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
    // Reload to swap the temporary id for the server-assigned one.
    createCard(columnId, title, details).then(reload).catch(reload);
  };

  // Move a card to the previous/next column (direction -1 / +1), appended to
  // the end of the target. A click-based alternative to dragging across columns.
  const handleMoveCard = (cardId: string, fromColumnId: string, direction: number) => {
    const fromIndex = board.columns.findIndex((c) => c.id === fromColumnId);
    const toIndex = fromIndex + direction;
    if (toIndex < 0 || toIndex >= board.columns.length) {
      return;
    }
    const toColumn = board.columns[toIndex];
    const position = toColumn.cardIds.length;

    setBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) => {
        if (column.id === fromColumnId) {
          return { ...column, cardIds: column.cardIds.filter((id) => id !== cardId) };
        }
        if (column.id === toColumn.id) {
          return { ...column, cardIds: [...column.cardIds, cardId] };
        }
        return column;
      }),
    }));

    updateCard(cardId, { columnId: toColumn.id, position }).catch(reload);
  };

  const handleEditCard = (cardId: string, title: string, details: string) => {
    setBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [cardId]: { ...prev.cards[cardId], title, details },
      },
    }));
    updateCard(cardId, { title, description: details }).catch(reload);
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    setBoard((prev) => ({
      ...prev,
      cards: Object.fromEntries(
        Object.entries(prev.cards).filter(([id]) => id !== cardId)
      ),
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: column.cardIds.filter((id) => id !== cardId) }
          : column
      ),
    }));
    deleteCard(cardId).catch(reload);
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <div className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col gap-8 px-6 pb-16 pt-12 lg:flex-row lg:items-start">
        <main className="flex min-w-0 flex-1 flex-col gap-10">
          <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                  Single Board Kanban
                </p>
                <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                  Kanban Studio
                </h1>
                <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                  Keep momentum visible. Rename columns, drag cards between stages,
                  and capture quick notes without getting buried in settings.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setChatOpen((open) => !open)}
                className="rounded-2xl bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold text-white shadow-[var(--shadow)] transition hover:brightness-110"
              >
                {chatOpen ? "Hide AI assistant" : "Ask AI assistant"}
              </button>
            </div>
          </header>

          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <section className="flex gap-5 overflow-x-auto pb-4">
              {board.columns.map((column, index) => (
                <KanbanColumn
                  key={column.id}
                  column={column}
                  columnIndex={index}
                  columnCount={board.columns.length}
                  cards={column.cardIds
                    .map((cardId) => board.cards[cardId])
                    .filter(Boolean)}
                  onRename={handleRenameColumn}
                  onCommitRename={handleCommitRename}
                  onAddCard={handleAddCard}
                  onEditCard={handleEditCard}
                  onDeleteCard={handleDeleteCard}
                  onMoveCard={handleMoveCard}
                />
              ))}
            </section>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>
        </main>

        {chatOpen && (
          <div className="w-full shrink-0 lg:sticky lg:top-12 lg:w-[380px]">
            <AIChatSidebar
              onBoardUpdate={setBoard}
              onClose={() => setChatOpen(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
};
