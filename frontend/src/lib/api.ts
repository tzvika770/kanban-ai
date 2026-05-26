import type { BoardData, Card, Column } from "@/lib/kanban";

// Backend wire format (see backend/app/schemas.py). Ids are integers; the
// client prefixes them (`col-`/`card-`) so column and card ids never collide
// as dnd-kit identifiers.
type WireColumn = { id: number; title: string; position: number };
type WireCard = {
  id: number;
  column_id: number;
  title: string;
  description: string | null;
  position: number;
};
type WireBoard = { columns: WireColumn[]; cards: WireCard[] };

export const columnDomId = (id: number) => `col-${id}`;
export const cardDomId = (id: number) => `card-${id}`;

/** Parse the numeric backend id out of a prefixed dom id (`card-12` -> 12). */
export const numericId = (domId: string): number => Number(domId.split("-")[1]);

export function mapBoard(wire: WireBoard): BoardData {
  const cards: Record<string, Card> = {};
  for (const c of wire.cards) {
    cards[cardDomId(c.id)] = {
      id: cardDomId(c.id),
      title: c.title,
      details: c.description ?? "",
    };
  }

  const columns: Column[] = [...wire.columns]
    .sort((a, b) => a.position - b.position)
    .map((col) => ({
      id: columnDomId(col.id),
      title: col.title,
      cardIds: wire.cards
        .filter((c) => c.column_id === col.id)
        .sort((a, b) => a.position - b.position)
        .map((c) => cardDomId(c.id)),
    }));

  return { columns, cards };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  const res = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (res.status === 401 && typeof window !== "undefined") {
    // Stale or expired token: clear it and send the user back to log in.
    localStorage.removeItem("auth_token");
    localStorage.removeItem("username");
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const fetchBoard = async (): Promise<BoardData> =>
  mapBoard(await request<WireBoard>("/kanban"));

// Returns the created card (with its real server id) so the caller can swap
// out the optimistic temporary id.
export const createCard = async (
  columnId: string,
  title: string,
  details: string
): Promise<Card> => {
  const c = await request<WireCard>("/cards", {
    method: "POST",
    body: JSON.stringify({
      column_id: numericId(columnId),
      title,
      description: details,
    }),
  });
  return { id: cardDomId(c.id), title: c.title, details: c.description ?? "" };
};

type CardUpdate = {
  title?: string;
  description?: string;
  columnId?: string;
  position?: number;
};

export const updateCard = (cardId: string, updates: CardUpdate) =>
  request(`/cards/${numericId(cardId)}`, {
    method: "PATCH",
    body: JSON.stringify({
      title: updates.title,
      description: updates.description,
      column_id: updates.columnId ? numericId(updates.columnId) : undefined,
      position: updates.position,
    }),
  });

export const deleteCard = (cardId: string) =>
  request(`/cards/${numericId(cardId)}`, { method: "DELETE" });

export const renameColumn = (columnId: string, title: string) =>
  request(`/columns/${numericId(columnId)}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });

export type AIChatResult = {
  response: string;
  board: BoardData;
};

export const aiChat = async (
  message: string,
  history: { role: "user" | "assistant"; content: string }[]
): Promise<AIChatResult> => {
  const data = await request<{ response: string; updated_board: WireBoard }>(
    "/ai/chat",
    { method: "POST", body: JSON.stringify({ message, history }) }
  );
  return { response: data.response, board: mapBoard(data.updated_board) };
};
