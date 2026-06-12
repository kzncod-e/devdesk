import pytest

from tests.conftest import register_and_login


async def seed(client, headers):
    pid = (await client.post("/api/v1/projects", headers=headers,
                             json={"name": "Nginx infra",
                                   "description": "proxy work"})).json()["id"]
    await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                      json={"title": "Configure nginx"})
    await client.post("/api/v1/snippets", headers=headers,
                      json={"title": "Nginx server block", "language": "nginx",
                            "code": "server {}", "tags": ["infra"]})
    await client.post("/api/v1/bookmarks", headers=headers,
                      json={"url": "https://nginx.org", "tags": ["nginx"]})
    return pid


@pytest.mark.asyncio
async def test_search_returns_grouped_owner_scoped_results(client):
    alice = await register_and_login(client, email="alice@test.dev")
    bob = await register_and_login(client, email="bob@test.dev")
    await seed(client, alice)

    r = await client.get("/api/v1/search?q=nginx", headers=alice)
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"projects", "tasks", "snippets", "bookmarks"}
    assert len(body["projects"]) == 1
    assert len(body["tasks"]) == 1
    assert len(body["snippets"]) == 1
    assert len(body["bookmarks"]) == 1
    assert body["tasks"][0]["title"] == "Configure nginx"

    # bob sees nothing of alice's
    r = await client.get("/api/v1/search?q=nginx", headers=bob)
    assert all(group == [] for group in r.json().values())


@pytest.mark.asyncio
async def test_search_limit_and_validation(client):
    headers = await register_and_login(client)
    for i in range(3):
        await client.post("/api/v1/snippets", headers=headers,
                          json={"title": f"Redis tip {i}", "language": "redis",
                                "code": "GET", "tags": []})

    r = await client.get("/api/v1/search?q=redis&limit=2", headers=headers)
    assert len(r.json()["snippets"]) == 2

    assert (await client.get("/api/v1/search", headers=headers)).status_code == 422
    assert (await client.get("/api/v1/search?q=", headers=headers)).status_code == 422


@pytest.mark.asyncio
async def test_search_requires_auth(client):
    assert (await client.get("/api/v1/search?q=x")).status_code in (401, 403)
