"use client";

import { useState, type FormEvent } from "react";
import { aiChat } from "@/lib/api";
import type { BoardData } from "@/lib/kanban";

type Message = { role: "user" | "assistant"; content: string };

type AIChatSidebarProps = {
  onBoardUpdate: (board: BoardData) => void;
  onClose: () => void;
};

export const AIChatSidebar = ({ onBoardUpdate, onClose }: AIChatSidebarProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (event: FormEvent) => {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) {
      return;
    }

    const history = messages;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    setError("");

    try {
      const { response, board } = await aiChat(text, history);
      setMessages((prev) => [...prev, { role: "assistant", content: response }]);
      onBoardUpdate(board);
    } catch {
      setError("The assistant is unavailable. Check the OpenRouter API key.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <aside className="flex h-[640px] w-full max-w-sm flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] shadow-[var(--shadow)]">
      <div className="flex items-center gap-3 border-b border-[var(--stroke)] px-5 py-4">
        <span className="h-2 w-10 rounded-full bg-[var(--secondary-purple)]" />
        <div className="flex-1">
          <h2 className="font-display text-lg font-semibold text-[var(--navy-dark)]">
            AI Assistant
          </h2>
          <p className="text-xs text-[var(--gray-text)]">
            Ask it to create, edit, or move cards.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close AI assistant"
          className="rounded-full border border-[var(--stroke)] px-3 py-1 text-sm font-semibold text-[var(--gray-text)] transition hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
        >
          &times;
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-4">
        {messages.length === 0 && (
          <p className="text-sm leading-6 text-[var(--gray-text)]">
            Try: &ldquo;Add a card to Backlog for the launch checklist&rdquo; or
            &ldquo;Move QA micro-interactions to Done&rdquo;.
          </p>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={
              message.role === "user"
                ? "self-end rounded-2xl rounded-br-sm bg-[var(--primary-blue)] px-4 py-2 text-sm text-white"
                : "self-start rounded-2xl rounded-bl-sm bg-[var(--surface)] px-4 py-2 text-sm text-[var(--navy-dark)]"
            }
          >
            {message.content}
          </div>
        ))}
        {loading && (
          <div className="self-start text-sm text-[var(--gray-text)]">Thinking...</div>
        )}
        {error && <div className="self-start text-sm text-[var(--secondary-purple)]">{error}</div>}
      </div>

      <form onSubmit={handleSend} className="flex gap-2 border-t border-[var(--stroke)] p-4">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask the assistant..."
          aria-label="Message the assistant"
          disabled={loading}
          className="flex-1 rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-full bg-[var(--secondary-purple)] px-5 py-2 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </aside>
  );
};
