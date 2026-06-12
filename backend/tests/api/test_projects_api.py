import pytest

from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_project_crud_flow(client):
    headers = await register_and_login(client)

    r = await client.post("/api/v1/projects", headers=headers,
                          json={"name": "DevDesk", "description": "workspace"})
    assert r.status_code == 201
    pid = r.json()["id"]

    r = await client.get("/api/v1/projects", headers=headers)
    assert r.status_code == 200
    assert [p["id"] for p in r.json()] == [pid]

    r = await client.patch(f"/api/v1/projects/{pid}", headers=headers,
                           json={"status": "archived"})
    assert r.status_code == 200
    assert r.json()["status"] == "archived"

    r = await client.delete(f"/api/v1/projects/{pid}", headers=headers)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/projects/{pid}", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_projects_are_owner_isolated(client):
    alice = await register_and_login(client, email="alice@test.dev")
    bob = await register_and_login(client, email="bob@test.dev")

    r = await client.post("/api/v1/projects", headers=alice, json={"name": "Secret"})
    pid = r.json()["id"]

    r = await client.get(f"/api/v1/projects/{pid}", headers=bob)
    assert r.status_code == 404  # not 403: don't leak existence
    r = await client.get("/api/v1/projects", headers=bob)
    assert r.json() == []


@pytest.mark.asyncio
async def test_projects_require_auth(client):
    r = await client.get("/api/v1/projects")
    assert r.status_code in (401, 403)
