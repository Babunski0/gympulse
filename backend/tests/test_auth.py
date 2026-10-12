from sqlalchemy import select

from app.core.db import SessionLocal
from app.models import User
from tests.conftest import auth_headers, login, register


def test_register_creates_account_with_hashed_password(client):  # US-01
    res = register(client, email="Ana@Example.com")
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "ana@example.com"
    assert body["role"] == "member"
    assert "password" not in body and "password_hash" not in body
    with SessionLocal() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")


def test_register_duplicate_email_is_rejected(client):  # US-01
    register(client)
    res = register(client, email="ANA@example.com")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "email_taken"
    with SessionLocal() as db:
        assert len(db.scalars(select(User)).all()) == 1


def test_register_validates_input(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "short", "full_name": "  "},
    )
    assert res.status_code == 422
    fields = {d["field"] for d in res.json()["error"]["details"]}
    assert fields == {"email", "password", "full_name"}


def test_login_and_me(client):  # US-02
    register(client)
    res = login(client)
    assert res.status_code == 200
    tokens = res.json()
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["full_name"] == "Ana Anić"


def test_login_wrong_password_or_unknown_email(client):  # US-02
    register(client)
    assert login(client, password="pogresna-lozinka").status_code == 401
    res = login(client, email="niko@example.com")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"


def test_private_endpoints_require_token(client):  # NFR-01
    assert client.get("/api/v1/me").status_code == 401
    bad = client.get("/api/v1/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401


def test_logout_revokes_access_and_refresh_tokens(client):  # US-02
    register(client)
    tokens = login(client).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 401


def test_refresh_rotates_tokens(client):
    register(client)
    tokens = login(client).json()
    res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 200
    new = res.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    # The old refresh token cannot be reused, and the old access token's session is closed.
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401
    old_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/api/v1/me", headers=old_headers).status_code == 401
    new_headers = {"Authorization": f"Bearer {new['access_token']}"}
    assert client.get("/api/v1/me", headers=new_headers).status_code == 200


def test_update_profile_name(client):  # US-13
    headers = auth_headers(client)
    res = client.put("/api/v1/me", json={"full_name": "Ana Petrović"}, headers=headers)
    assert res.status_code == 200
    relogin = login(client).json()["access_token"]
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {relogin}"})
    assert me.json()["full_name"] == "Ana Petrović"


def test_login_is_rate_limited(client):
    register(client)
    codes = [login(client, password="pogresna-lozinka").status_code for _ in range(25)]
    assert 429 in codes
