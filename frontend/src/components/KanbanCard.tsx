import { useState, type FormEvent } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onEdit: (cardId: string, title: string, details: string) => void;
  onDelete: (cardId: string) => void;
  onMoveLeft?: () => void;
  onMoveRight?: () => void;
};

export const KanbanCard = ({
  card,
  onEdit,
  onDelete,
  onMoveLeft,
  onMoveRight,
}: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState({ title: card.title, details: card.details });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  // Editing mode renders a plain form without drag listeners so text can be
  // selected and typed without starting a drag.
  if (isEditing) {
    const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!draft.title.trim()) {
        return;
      }
      onEdit(card.id, draft.title.trim(), draft.details.trim());
      setIsEditing(false);
    };

    return (
      <form
        onSubmit={handleSubmit}
        className="space-y-3 rounded-2xl border border-[var(--primary-blue)] bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]"
      >
        <input
          value={draft.title}
          onChange={(event) => setDraft((prev) => ({ ...prev, title: event.target.value }))}
          aria-label="Card title"
          className="w-full rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm font-medium text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
          required
        />
        <textarea
          value={draft.details}
          onChange={(event) => setDraft((prev) => ({ ...prev, details: event.target.value }))}
          aria-label="Card details"
          rows={3}
          className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--gray-text)] outline-none focus:border-[var(--primary-blue)]"
        />
        <div className="flex items-center gap-2">
          <button
            type="submit"
            className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110"
          >
            Save
          </button>
          <button
            type="button"
            onClick={() => {
              setDraft({ title: card.title, details: card.details });
              setIsEditing(false);
            }}
            className="rounded-full border border-[var(--stroke)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
          >
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]"
      )}
      {...attributes}
      {...listeners}
      data-testid={`card-${card.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
            {card.title}
          </h4>
          <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
            {card.details}
          </p>
        </div>
        <div className="flex shrink-0 flex-col gap-1">
          <button
            type="button"
            onClick={() => {
              setDraft({ title: card.title, details: card.details });
              setIsEditing(true);
            }}
            className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--primary-blue)] transition hover:border-[var(--stroke)]"
            aria-label={`Edit ${card.title}`}
          >
            Edit
          </button>
          <button
            type="button"
            onClick={() => onDelete(card.id)}
            className="rounded-full border border-transparent px-2 py-1 text-xs font-semibold text-[var(--gray-text)] transition hover:border-[var(--stroke)] hover:text-[var(--navy-dark)]"
            aria-label={`Delete ${card.title}`}
          >
            Remove
          </button>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-[var(--stroke)] pt-3">
        <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Move
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onMoveLeft}
            disabled={!onMoveLeft}
            aria-label={`Move ${card.title} to previous column`}
            className="rounded-full border border-[var(--stroke)] px-3 py-1 text-sm font-semibold text-[var(--primary-blue)] transition hover:border-[var(--primary-blue)] disabled:cursor-not-allowed disabled:border-transparent disabled:text-[var(--stroke)]"
          >
            &larr;
          </button>
          <button
            type="button"
            onClick={onMoveRight}
            disabled={!onMoveRight}
            aria-label={`Move ${card.title} to next column`}
            className="rounded-full border border-[var(--stroke)] px-3 py-1 text-sm font-semibold text-[var(--primary-blue)] transition hover:border-[var(--primary-blue)] disabled:cursor-not-allowed disabled:border-transparent disabled:text-[var(--stroke)]"
          >
            &rarr;
          </button>
        </div>
      </div>
    </article>
  );
};
