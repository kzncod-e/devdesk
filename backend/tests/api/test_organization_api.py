"""Tests for Phase 2.7: collections, tag registry, saved filters."""
import pytest

from tests.conftest import register_and_login


# ── Collections ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_collection_crud_and_snippet_filtering(client):
    headers = await register_and_login(client)

    col = (await client.post("/api/v1/collections", headers=headers,
                             json={"name": "Backend", "kind": "snippet"})).json()
    assert col["kind"] == "snippet" and col["parent_id"] is None

    # snippet assigned to the collection
    s = await client.post("/api/v1/snippets", headers=headers,
                          json={"title": "DB pool", "language": "py", "code": "x=1",
                                "tags": [], "notes": "", "collection_id": col["id"]})
    assert s.status_code == 201 and s.json()["collection_id"] == col["id"]
    # and one without
    await client.post("/api/v1/snippets", headers=headers,
                      json={"title": "Loose", "language": "py", "code": "y=2", "tags": []})

    filtered = (await client.get(f"/api/v1/snippets?collection_id={col['id']}",
                                 headers=headers)).json()
    assert [s["title"] for s in filtered] == ["DB pool"]


@pytest.mark.asyncio
async def test_collection_nesting_and_kind_guard(client):
    headers = await register_and_login(client)
    parent = (await client.post("/api/v1/collections", headers=headers,
                                json={"name": "Parent", "kind": "snippet"})).json()
    child = await client.post("/api/v1/collections", headers=headers,
                              json={"name": "Child", "kind": "snippet",
                                    "parent_id": parent["id"]})
    assert child.status_code == 201 and child.json()["parent_id"] == parent["id"]

    # parent of a different kind is rejected
    bad = await client.post("/api/v1/collections", headers=headers,
                            json={"name": "Mismatch", "kind": "bookmark",
                                  "parent_id": parent["id"]})
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_collection_list_filtered_by_kind(client):
    headers = await register_and_login(client)
    await client.post("/api/v1/collections", headers=headers,
                      json={"name": "Snips", "kind": "snippet"})
    await client.post("/api/v1/collections", headers=headers,
                      json={"name": "Marks", "kind": "bookmark"})
    snip_cols = (await client.get("/api/v1/collections?kind=snippet", headers=headers)).json()
    assert {c["name"] for c in snip_cols} == {"Snips"}


# ── Tag registry ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tags_autopopulate_from_snippets_and_recolor(client):
    headers = await register_and_login(client)
    await client.post("/api/v1/snippets", headers=headers,
                      json={"title": "Tagged", "language": "py", "code": "z=3",
                            "tags": ["api", "db"], "notes": ""})

    tags = (await client.get("/api/v1/tags", headers=headers)).json()
    by_name = {t["name"]: t for t in tags}
    assert {"api", "db"} <= set(by_name)
    assert by_name["api"]["color"] == "#6366f1"  # default

    # recolor
    r = await client.patch(f"/api/v1/tags/{by_name['api']['id']}", headers=headers,
                           json={"color": "#ff0000"})
    assert r.status_code == 200 and r.json()["color"] == "#ff0000"

    # invalid hex rejected
    bad = await client.patch(f"/api/v1/tags/{by_name['db']['id']}", headers=headers,
                             json={"color": "red"})
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_tags_dedup_across_entities_and_workspace_scoped(client):
    alice = await register_and_login(client, email="alice@test.dev")
    await client.post("/api/v1/snippets", headers=alice,
                      json={"title": "A", "language": "py", "code": "1", "tags": ["shared"]})
    await client.post("/api/v1/bookmarks", headers=alice,
                      json={"url": "https://example.com", "tags": ["shared", "web"]})
    tags = (await client.get("/api/v1/tags", headers=alice)).json()
    names = [t["name"] for t in tags]
    assert names.count("shared") == 1  # deduped in the registry

    bob = await register_and_login(client, email="bob@test.dev")
    assert (await client.get("/api/v1/tags", headers=bob)).json() == []


# ── Saved filters ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_saved_filters_crud_and_user_isolation(client):
    alice = await register_and_login(client, email="alice@test.dev")
    created = await client.post("/api/v1/saved-filters", headers=alice,
                                json={"name": "Python snippets", "kind": "snippet",
                                      "query": {"language": "py"}})
    assert created.status_code == 201
    fid = created.json()["id"]

    mine = (await client.get("/api/v1/saved-filters?kind=snippet", headers=alice)).json()
    assert [f["name"] for f in mine] == ["Python snippets"]
    assert mine[0]["query"] == {"language": "py"}

    # a workspace co-member doesn't see another user's saved filters
    ws_id = alice["X-Workspace-Id"]
    inv = await client.post(f"/api/v1/workspaces/{ws_id}/invites", headers=alice,
                            json={"email": "bob@test.dev", "role": "member"})
    bob = await register_and_login(client, email="bob@test.dev")
    await client.post("/api/v1/invites/accept", headers=bob, json={"token": inv.json()["token"]})
    bob_ws = {**bob, "X-Workspace-Id": str(ws_id)}
    assert (await client.get("/api/v1/saved-filters", headers=bob_ws)).json() == []

    # delete
    assert (await client.delete(f"/api/v1/saved-filters/{fid}", headers=alice)).status_code == 204
    assert (await client.get("/api/v1/saved-filters", headers=alice)).json() == []


@pytest.mark.asyncio
async def test_saved_filter_invalid_kind_rejected(client):
    headers = await register_and_login(client)
    r = await client.post("/api/v1/saved-filters", headers=headers,
                          json={"name": "bad", "kind": "nonsense", "query": {}})
    assert r.status_code == 422
