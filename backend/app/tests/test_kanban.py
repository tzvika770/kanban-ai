def test_board_is_seeded(auth_client):
    board = auth_client.get("/api/kanban").json()
    assert [c["title"] for c in board["columns"]] == [
        "Backlog",
        "Discovery",
        "In Progress",
        "Review",
        "Done",
    ]
    assert len(board["cards"]) == 8


def test_create_card(auth_client):
    board = auth_client.get("/api/kanban").json()
    column_id = board["columns"][1]["id"]  # Discovery (1 seeded card)

    resp = auth_client.post(
        "/api/cards",
        json={"column_id": column_id, "title": "Fresh card", "description": "d"},
    )
    assert resp.status_code == 201
    card = resp.json()
    assert card["title"] == "Fresh card"
    assert card["column_id"] == column_id
    assert card["position"] == 1  # appended after the existing card


def test_create_card_unknown_column(auth_client):
    auth_client.get("/api/kanban")
    resp = auth_client.post(
        "/api/cards", json={"column_id": 9999, "title": "x", "description": ""}
    )
    assert resp.status_code == 404


def test_update_card_title(auth_client):
    board = auth_client.get("/api/kanban").json()
    card_id = board["cards"][0]["id"]
    resp = auth_client.patch(f"/api/cards/{card_id}", json={"title": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed"


def test_move_card_between_columns(auth_client):
    board = auth_client.get("/api/kanban").json()
    backlog, discovery = board["columns"][0]["id"], board["columns"][1]["id"]
    card = next(c for c in board["cards"] if c["column_id"] == backlog)

    resp = auth_client.patch(
        f"/api/cards/{card['id']}", json={"column_id": discovery, "position": 0}
    )
    assert resp.status_code == 200
    moved = resp.json()
    assert moved["column_id"] == discovery
    assert moved["position"] == 0

    # Source column positions stay contiguous from 0.
    board = auth_client.get("/api/kanban").json()
    backlog_positions = sorted(
        c["position"] for c in board["cards"] if c["column_id"] == backlog
    )
    assert backlog_positions == list(range(len(backlog_positions)))


def test_delete_card(auth_client):
    board = auth_client.get("/api/kanban").json()
    card_id = board["cards"][0]["id"]
    assert auth_client.delete(f"/api/cards/{card_id}").status_code == 200

    board = auth_client.get("/api/kanban").json()
    assert card_id not in [c["id"] for c in board["cards"]]
    assert len(board["cards"]) == 7


def test_delete_missing_card(auth_client):
    auth_client.get("/api/kanban")
    assert auth_client.delete("/api/cards/9999").status_code == 404


def test_rename_column(auth_client):
    board = auth_client.get("/api/kanban").json()
    column_id = board["columns"][0]["id"]
    resp = auth_client.patch(f"/api/columns/{column_id}", json={"title": "Todo"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Todo"
