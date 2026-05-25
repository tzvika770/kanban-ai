from app import ai
from app.ai import AIOutput
from app.schemas import Mutation


def test_ai_test_endpoint(auth_client, monkeypatch):
    monkeypatch.setattr(ai, "ai_test", lambda: "4")
    resp = auth_client.post("/api/ai/test")
    assert resp.status_code == 200
    assert resp.json() == {"response": "4"}


def test_ai_chat_empty_message(auth_client):
    resp = auth_client.post("/api/ai/chat", json={"message": "   "})
    assert resp.status_code == 400


def test_ai_chat_applies_create_mutation(auth_client, monkeypatch):
    board = auth_client.get("/api/kanban").json()
    column_id = board["columns"][0]["id"]
    before = len(board["cards"])

    def fake_chat(message, history, board_out):
        return AIOutput(
            response="Added a card.",
            mutations=[
                Mutation(
                    type="create_card",
                    column_id=column_id,
                    title="AI card",
                    description="from the assistant",
                )
            ],
        )

    monkeypatch.setattr(ai, "ai_chat", fake_chat)

    resp = auth_client.post("/api/ai/chat", json={"message": "add a card"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["response"] == "Added a card."
    assert len(body["mutations"]) == 1
    titles = [c["title"] for c in body["updated_board"]["cards"]]
    assert "AI card" in titles
    assert len(body["updated_board"]["cards"]) == before + 1


def test_ai_chat_skips_invalid_mutation(auth_client, monkeypatch):
    auth_client.get("/api/kanban")

    def fake_chat(message, history, board_out):
        return AIOutput(
            response="Tried.",
            mutations=[Mutation(type="delete_card", card_id=999999)],
        )

    monkeypatch.setattr(ai, "ai_chat", fake_chat)

    resp = auth_client.post("/api/ai/chat", json={"message": "delete ghost"})
    assert resp.status_code == 200
    # Invalid mutation referencing a missing card is skipped, not applied.
    assert resp.json()["mutations"] == []
