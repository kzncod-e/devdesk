import pytest

from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_signup_provisions_personal_workspace(client):
    headers = await register_and_login(client)
    r = await client.get("/api/v1/workspaces", headers=headers)
    assert r.status_code == 200
    spaces = r.json()
    assert len(spaces) == 1
    assert spaces[0]["role"] == "owner"


@pytest.mark.asyncio
async def test_content_falls_back_to_default_workspace_without_header(client):
    headers = await register_and_login(client)
    no_ws = {"Authorization": headers["Authorization"]}  # drop X-Workspace-Id
    r = await client.post("/api/v1/projects", headers=no_ws, json={"name": "Default ws"})
    assert r.status_code == 201
    # and it's visible when scoping explicitly to the personal workspace
    listed = await client.get("/api/v1/projects", headers=headers)
    assert [p["name"] for p in listed.json()] == ["Default ws"]


@pytest.mark.asyncio
async def test_create_additional_workspace(client):
    headers = await register_and_login(client)
    r = await client.post("/api/v1/workspaces", headers=headers, json={"name": "Team X"})
    assert r.status_code == 201 and r.json()["role"] == "owner"
    r = await client.get("/api/v1/workspaces", headers=headers)
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_invite_accept_grants_shared_access(client):
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = alice["X-Workspace-Id"]
    pid = (await client.post("/api/v1/projects", headers=alice,
                             json={"name": "Shared"})).json()["id"]

    bob = await register_and_login(client, email="bob@test.dev")
    # alice invites bob as an editor
    r = await client.post(f"/api/v1/workspaces/{ws_id}/invites", headers=alice,
                          json={"email": "bob@test.dev", "role": "editor"})
    assert r.status_code == 201
    token = r.json()["token"]

    r = await client.post("/api/v1/invites/accept", headers=bob, json={"token": token})
    assert r.status_code == 200 and r.json()["role"] == "editor"

    # bob now operates inside alice's workspace and sees the shared project
    bob_ws = {**bob, "X-Workspace-Id": ws_id}
    projects = (await client.get("/api/v1/projects", headers=bob_ws)).json()
    assert pid in [p["id"] for p in projects]
    # editor may create content
    r = await client.post(f"/api/v1/projects/{pid}/tasks", headers=bob_ws,
                          json={"title": "Bob's task"})
    assert r.status_code == 201

    members = (await client.get(f"/api/v1/workspaces/{ws_id}/members", headers=alice)).json()
    assert {m["email"] for m in members} == {"alice@test.dev", "bob@test.dev"}


@pytest.mark.asyncio
async def test_viewer_cannot_write(client):
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = alice["X-Workspace-Id"]
    carol = await register_and_login(client, email="carol@test.dev")
    token = (await client.post(f"/api/v1/workspaces/{ws_id}/invites", headers=alice,
                               json={"email": "carol@test.dev", "role": "viewer"})).json()["token"]
    await client.post("/api/v1/invites/accept", headers=carol, json={"token": token})

    carol_ws = {**carol, "X-Workspace-Id": ws_id}
    assert (await client.get("/api/v1/projects", headers=carol_ws)).status_code == 200
    assert (await client.post("/api/v1/projects", headers=carol_ws,
                              json={"name": "Nope"})).status_code == 403


@pytest.mark.asyncio
async def test_non_member_is_blocked(client):
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = alice["X-Workspace-Id"]
    dave = await register_and_login(client, email="dave@test.dev")
    dave_ws = {**dave, "X-Workspace-Id": ws_id}
    assert (await client.get("/api/v1/projects", headers=dave_ws)).status_code == 403


@pytest.mark.asyncio
async def test_last_owner_cannot_be_removed(client):
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = alice["X-Workspace-Id"]
    me = (await client.get("/api/v1/auth/me", headers=alice)).json()
    r = await client.delete(f"/api/v1/workspaces/{ws_id}/members/{me['id']}", headers=alice)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_member_management_requires_permission(client):
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = alice["X-Workspace-Id"]
    bob = await register_and_login(client, email="bob@test.dev")
    token = (await client.post(f"/api/v1/workspaces/{ws_id}/invites", headers=alice,
                               json={"email": "bob@test.dev", "role": "member"})).json()["token"]
    await client.post("/api/v1/invites/accept", headers=bob, json={"token": token})

    # a plain member cannot invite others
    bob_ws = {**bob, "X-Workspace-Id": ws_id}
    r = await client.post(f"/api/v1/workspaces/{ws_id}/invites", headers=bob_ws,
                          json={"email": "x@test.dev", "role": "member"})
    assert r.status_code == 403
