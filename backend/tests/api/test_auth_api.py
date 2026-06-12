import pytest


@pytest.mark.asyncio
async def test_register_login_me_flow(client):
    r = await client.post("/api/v1/auth/register",
                          json={"email": "a@b.c", "password": "pw123456", "name": "A"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@b.c"
    assert "password" not in r.json() and "password_hash" not in r.json()

    r = await client.post("/api/v1/auth/login",
                          json={"email": "a@b.c", "password": "pw123456"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"

    r = await client.get("/api/v1/auth/me",
                         headers={"Authorization": f"Bearer {body['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.c"


@pytest.mark.asyncio
async def test_duplicate_register_409(client):
    payload = {"email": "a@b.c", "password": "pw123456", "name": "A"}
    await client.post("/api/v1/auth/register", json=payload)
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409
    assert r.json()["code"] == "conflict"


@pytest.mark.asyncio
async def test_bad_login_401_and_me_requires_auth(client):
    r = await client.post("/api/v1/auth/login",
                          json={"email": "no@x.y", "password": "nope1234"})
    assert r.status_code == 401
    r = await client.get("/api/v1/auth/me")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_issues_new_tokens(client):
    await client.post("/api/v1/auth/register",
                      json={"email": "a@b.c", "password": "pw123456", "name": "A"})
    login = await client.post("/api/v1/auth/login",
                              json={"email": "a@b.c", "password": "pw123456"})
    refresh_token = login.json()["refresh_token"]
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_login_sets_httponly_refresh_cookie(client):
    await client.post("/api/v1/auth/register",
                      json={"email": "a@b.c", "password": "pw123456", "name": "A"})
    r = await client.post("/api/v1/auth/login",
                          json={"email": "a@b.c", "password": "pw123456"})
    set_cookie = r.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie


@pytest.mark.asyncio
async def test_refresh_works_with_cookie_only(client):
    await client.post("/api/v1/auth/register",
                      json={"email": "a@b.c", "password": "pw123456", "name": "A"})
    await client.post("/api/v1/auth/login",
                      json={"email": "a@b.c", "password": "pw123456"})
    # client cookie jar now holds the refresh cookie; send no body at all
    r = await client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    assert r.json()["access_token"]
    # rotation: a fresh cookie is set on every refresh
    assert "refresh_token=" in r.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_register_validates_input(client):
    r = await client.post("/api/v1/auth/register",
                          json={"email": "not-an-email", "password": "short", "name": ""})
    assert r.status_code == 422
