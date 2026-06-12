import pytest

from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_bookmark_create_triggers_background_metadata_fetch(client):
    headers = await register_and_login(client)
    r = await client.post("/api/v1/bookmarks", headers=headers,
                          json={"url": "https://example.com/docs", "tags": ["docs"]})
    assert r.status_code == 201
    body = r.json()
    bid = body["id"]
    # response returns immediately, before metadata exists
    assert body["title"] == "" and body["fetched_meta"] == {}

    # ASGITransport runs background tasks before the response cycle completes,
    # so the stubbed fetcher has populated metadata by the next request
    r = await client.get(f"/api/v1/bookmarks/{bid}", headers=headers)
    fetched = r.json()
    assert fetched["title"] == "Stub Page"
    assert fetched["description"] == "Stubbed description"
    assert fetched["favicon"] == "https://example.com/stub-icon.png"


@pytest.mark.asyncio
async def test_bookmark_crud_filters_and_isolation(client):
    alice = await register_and_login(client, email="alice@test.dev")
    bob = await register_and_login(client, email="bob@test.dev")
    pid = (await client.post("/api/v1/projects", headers=alice,
                             json={"name": "P"})).json()["id"]

    b1 = (await client.post("/api/v1/bookmarks", headers=alice,
                            json={"url": "https://a.example", "tags": ["docs"],
                                  "project_id": pid})).json()
    await client.post("/api/v1/bookmarks", headers=alice,
                      json={"url": "https://b.example", "tags": ["api"]})

    assert len((await client.get("/api/v1/bookmarks", headers=alice)).json()) == 2
    r = await client.get("/api/v1/bookmarks?tag=docs", headers=alice)
    assert [b["url"] for b in r.json()] == ["https://a.example/"]
    r = await client.get(f"/api/v1/bookmarks?project_id={pid}", headers=alice)
    assert len(r.json()) == 1

    # owner isolation
    assert (await client.get(f"/api/v1/bookmarks/{b1['id']}", headers=bob)).status_code == 404
    assert (await client.get("/api/v1/bookmarks", headers=bob)).json() == []

    # edit tags/title
    r = await client.patch(f"/api/v1/bookmarks/{b1['id']}", headers=alice,
                           json={"title": "Renamed", "tags": ["docs", "ref"]})
    assert r.json()["title"] == "Renamed" and r.json()["tags"] == ["docs", "ref"]

    r = await client.delete(f"/api/v1/bookmarks/{b1['id']}", headers=alice)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_bookmark_auth_validation_and_summary_count(client):
    assert (await client.get("/api/v1/bookmarks")).status_code in (401, 403)
    headers = await register_and_login(client)

    r = await client.post("/api/v1/bookmarks", headers=headers,
                          json={"url": "not a url"})
    assert r.status_code == 422

    pid = (await client.post("/api/v1/projects", headers=headers,
                             json={"name": "P"})).json()["id"]
    await client.post("/api/v1/bookmarks", headers=headers,
                      json={"url": "https://x.example", "project_id": pid})
    r = await client.get(f"/api/v1/projects/{pid}/summary", headers=headers)
    assert r.json()["bookmarks"] == 1
