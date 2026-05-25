def test_login_success(client):
    resp = client.post(
        "/api/auth/login", json={"username": "user", "password": "password"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["username"] == "user"
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client):
    resp = client.post(
        "/api/auth/login", json={"username": "user", "password": "nope"}
    )
    assert resp.status_code == 401


def test_kanban_requires_auth(client):
    assert client.get("/api/kanban").status_code == 401


def test_kanban_rejects_bad_token(client):
    resp = client.get("/api/kanban", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401
