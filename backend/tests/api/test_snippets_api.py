import pytest

from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_snippet_crud_flow(client):
    headers = await register_and_login(client)

    r = await client.post("/api/v1/snippets", headers=headers,
                          json={"title": "Fetch wrapper", "language": "typescript",
                                "code": "export {}", "tags": ["nuxt", "http"]})
    assert r.status_code == 201
    body = r.json()
    sid = body["id"]
    assert body["tags"] == ["nuxt", "http"] and body["project_id"] is None

    r = await client.get(f"/api/v1/snippets/{sid}", headers=headers)
    assert r.status_code == 200 and r.json()["title"] == "Fetch wrapper"

    r = await client.patch(f"/api/v1/snippets/{sid}", headers=headers,
                           json={"title": "Renamed", "tags": ["nuxt"]})
    assert r.status_code == 200
    assert r.json()["title"] == "Renamed" and r.json()["tags"] == ["nuxt"]

    r = await client.delete(f"/api/v1/snippets/{sid}", headers=headers)
    assert r.status_code == 204
    assert (await client.get(f"/api/v1/snippets/{sid}", headers=headers)).status_code == 404


@pytest.mark.asyncio
async def test_snippet_filters(client):
    headers = await register_and_login(client)
    r = await client.post("/api/v1/projects", headers=headers, json={"name": "P"})
    pid = r.json()["id"]

    await client.post("/api/v1/snippets", headers=headers,
                      json={"title": "A", "language": "python", "code": "x",
                            "tags": ["api"], "project_id": pid})
    await client.post("/api/v1/snippets", headers=headers,
                      json={"title": "B", "language": "sql", "code": "x",
                            "tags": ["db"]})

    r = await client.get("/api/v1/snippets", headers=headers)
    assert len(r.json()) == 2
    r = await client.get("/api/v1/snippets?language=python", headers=headers)
    assert [s["title"] for s in r.json()] == ["A"]
    r = await client.get("/api/v1/snippets?tag=db", headers=headers)
    assert [s["title"] for s in r.json()] == ["B"]
    r = await client.get(f"/api/v1/snippets?project_id={pid}", headers=headers)
    assert [s["title"] for s in r.json()] == ["A"]


@pytest.mark.asyncio
async def test_snippet_project_link_validated_and_owner_isolated(client):
    alice = await register_and_login(client, email="alice@test.dev")
    bob = await register_and_login(client, email="bob@test.dev")

    r = await client.post("/api/v1/projects", headers=alice, json={"name": "AliceP"})
    alice_pid = r.json()["id"]

    # bob cannot attach his snippet to alice's project
    r = await client.post("/api/v1/snippets", headers=bob,
                          json={"title": "Hax", "language": "py", "code": "x",
                                "project_id": alice_pid})
    assert r.status_code == 404

    r = await client.post("/api/v1/snippets", headers=alice,
                          json={"title": "Secret", "language": "py", "code": "x"})
    sid = r.json()["id"]
    assert (await client.get(f"/api/v1/snippets/{sid}", headers=bob)).status_code == 404
    assert (await client.get("/api/v1/snippets", headers=bob)).json() == []


@pytest.mark.asyncio
async def test_snippet_auth_and_validation(client):
    assert (await client.get("/api/v1/snippets")).status_code in (401, 403)
    headers = await register_and_login(client)
    r = await client.post("/api/v1/snippets", headers=headers,
                          json={"title": "", "language": "", "code": "x"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_project_delete_detaches_snippets(client):
    headers = await register_and_login(client)
    pid = (await client.post("/api/v1/projects", headers=headers,
                             json={"name": "P"})).json()["id"]
    sid = (await client.post("/api/v1/snippets", headers=headers,
                             json={"title": "S", "language": "py", "code": "x",
                                   "project_id": pid})).json()["id"]

    r = await client.get(f"/api/v1/projects/{pid}/summary", headers=headers)
    assert r.json()["snippets"] == 1

    await client.delete(f"/api/v1/projects/{pid}", headers=headers)
    r = await client.get(f"/api/v1/snippets/{sid}", headers=headers)
    assert r.status_code == 200
    assert r.json()["project_id"] is None
