import pytest

from tests.conftest import register_and_login


async def make_task(client, headers, title="T"):
    pid = (await client.post("/api/v1/projects", headers=headers, json={"name": "P"})).json()["id"]
    r = await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers, json={"title": title})
    return r.json()["id"]


@pytest.mark.asyncio
async def test_comment_crud_flow(client):
    headers = await register_and_login(client)
    me = (await client.get("/api/v1/auth/me", headers=headers)).json()["id"]
    tid = await make_task(client, headers)

    # create (self-mention is a valid member, so it's accepted and de-duped server-side)
    r = await client.post("/api/v1/comments", headers=headers, json={
        "entity_type": "task", "entity_id": tid, "body": "First", "mention_ids": [me],
    })
    assert r.status_code == 201
    cid = r.json()["id"]
    assert r.json()["author"]["id"] == me
    assert r.json()["edited_at"] is None

    # list
    r = await client.get(f"/api/v1/comments?entity_type=task&entity_id={tid}", headers=headers)
    assert r.status_code == 200
    assert [c["body"] for c in r.json()] == ["First"]

    # edit
    r = await client.patch(f"/api/v1/comments/{cid}", headers=headers, json={"body": "First (edited)"})
    assert r.status_code == 200
    assert r.json()["body"] == "First (edited)" and r.json()["edited_at"] is not None

    # threaded reply
    r = await client.post("/api/v1/comments", headers=headers, json={
        "entity_type": "task", "entity_id": tid, "body": "reply", "parent_id": cid,
    })
    assert r.status_code == 201 and r.json()["parent_id"] == cid

    # delete (soft) — drops out of the list
    assert (await client.delete(f"/api/v1/comments/{cid}", headers=headers)).status_code == 204
    bodies = [c["body"] for c in (await client.get(
        f"/api/v1/comments?entity_type=task&entity_id={tid}", headers=headers)).json()]
    assert bodies == ["reply"]


@pytest.mark.asyncio
async def test_comments_are_workspace_isolated(client):
    alice = await register_and_login(client, email="alice@test.dev")
    bob = await register_and_login(client, email="bob@test.dev")
    tid = await make_task(client, alice)

    # Bob (a member only of his own workspace) cannot see or comment on Alice's task.
    assert (await client.get(
        f"/api/v1/comments?entity_type=task&entity_id={tid}", headers=bob)).status_code == 404
    assert (await client.post("/api/v1/comments", headers=bob, json={
        "entity_type": "task", "entity_id": tid, "body": "hax"})).status_code == 404


@pytest.mark.asyncio
async def test_invalid_mentions_dropped_not_fatal(client):
    headers = await register_and_login(client)
    tid = await make_task(client, headers)
    # 999999 isn't a member — it must be silently dropped, comment still created.
    r = await client.post("/api/v1/comments", headers=headers, json={
        "entity_type": "task", "entity_id": tid, "body": "hi @ghost", "mention_ids": [999999],
    })
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_comments_require_auth_and_validate(client):
    headers = await register_and_login(client)
    tid = await make_task(client, headers)

    assert (await client.get(
        f"/api/v1/comments?entity_type=task&entity_id={tid}")).status_code in (401, 403)
    # empty body and unsupported entity type are rejected by the schema
    assert (await client.post("/api/v1/comments", headers=headers, json={
        "entity_type": "task", "entity_id": tid, "body": ""})).status_code == 422
    assert (await client.post("/api/v1/comments", headers=headers, json={
        "entity_type": "snippet", "entity_id": tid, "body": "x"})).status_code == 422
