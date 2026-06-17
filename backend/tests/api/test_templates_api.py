"""Tests for /templates — capture, use (atomic instantiate), gallery, RBAC."""
import pytest

from tests.conftest import register_and_login


async def _make_project_with_content(client, headers, *, name="Starter") -> int:
    pid = (await client.post("/api/v1/projects", headers=headers,
                             json={"name": name, "description": "seed",
                                   "color": "#6366f1"})).json()["id"]
    await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                      json={"title": "First task", "priority": "high"})
    await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                      json={"title": "Second task"})
    await client.post("/api/v1/snippets", headers=headers,
                      json={"title": "Setup", "language": "bash", "code": "echo hi",
                            "tags": ["init"], "notes": "", "project_id": pid})
    return pid


# ── capture + use (project) ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_capture_project_serializes_children(client):
    headers = await register_and_login(client)
    pid = await _make_project_with_content(client, headers)

    r = await client.post("/api/v1/templates/capture", headers=headers,
                          json={"kind": "project", "source_id": pid,
                                "name": "Starter kit", "description": "scaffold"})
    assert r.status_code == 201
    body = r.json()
    assert body["kind"] == "project"
    assert body["use_count"] == 0
    payload = body["payload"]
    assert payload["project"]["name"] == "Starter"
    assert len(payload["tasks"]) == 2
    assert len(payload["snippets"]) == 1
    assert payload["tasks"][0]["priority"] == "high"


@pytest.mark.asyncio
async def test_use_project_template_instantiates_everything(client):
    headers = await register_and_login(client)
    pid = await _make_project_with_content(client, headers)
    tpl = (await client.post("/api/v1/templates/capture", headers=headers,
                             json={"kind": "project", "source_id": pid,
                                   "name": "Starter kit"})).json()

    r = await client.post(f"/api/v1/templates/{tpl['id']}/use", headers=headers)
    assert r.status_code == 200
    new_pid = r.json()["project_id"]
    assert new_pid != pid

    # new project carries the captured tasks + snippet
    tasks = (await client.get(f"/api/v1/projects/{new_pid}/tasks", headers=headers)).json()
    assert {t["title"] for t in tasks} == {"First task", "Second task"}
    snippets = (await client.get(f"/api/v1/snippets?project_id={new_pid}",
                                 headers=headers)).json()
    assert len(snippets) == 1 and snippets[0]["title"] == "Setup"

    # use_count incremented
    detail = (await client.get(f"/api/v1/templates/{tpl['id']}", headers=headers)).json()
    assert detail["use_count"] == 1


# ── capture + use (snippet) ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_capture_and_use_snippet_template(client):
    headers = await register_and_login(client)
    sid = (await client.post("/api/v1/snippets", headers=headers,
                             json={"title": "Debounce", "language": "ts",
                                   "code": "const x = 1", "tags": ["util"],
                                   "notes": "handy"})).json()["id"]

    tpl = (await client.post("/api/v1/templates/capture", headers=headers,
                             json={"kind": "snippet", "source_id": sid,
                                   "name": "Debounce util"})).json()
    assert tpl["payload"]["snippet"]["code"] == "const x = 1"

    r = await client.post(f"/api/v1/templates/{tpl['id']}/use", headers=headers)
    assert r.status_code == 200
    new_sid = r.json()["snippet_id"]
    new = (await client.get(f"/api/v1/snippets/{new_sid}", headers=headers)).json()
    assert new["title"] == "Debounce" and new["language"] == "ts"


# ── visibility / RBAC ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_member_cannot_publish_public_template(client):
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = alice["X-Workspace-Id"]
    pid = await _make_project_with_content(client, alice)

    bob = await register_and_login(client, email="bob@test.dev")
    inv = await client.post(f"/api/v1/workspaces/{ws_id}/invites", headers=alice,
                            json={"email": "bob@test.dev", "role": "member"})
    await client.post("/api/v1/invites/accept", headers=bob, json={"token": inv.json()["token"]})
    bob_ws = {**bob, "X-Workspace-Id": str(ws_id)}

    # member may capture as workspace-visibility
    ok = await client.post("/api/v1/templates/capture", headers=bob_ws,
                           json={"kind": "project", "source_id": pid,
                                 "name": "ws tpl", "visibility": "workspace"})
    assert ok.status_code == 201

    # but not publish public (needs workspace:manage)
    denied = await client.post("/api/v1/templates/capture", headers=bob_ws,
                               json={"kind": "project", "source_id": pid,
                                     "name": "public tpl", "visibility": "public"})
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_gallery_is_public_and_lists_only_public(client):
    headers = await register_and_login(client)
    pid = await _make_project_with_content(client, headers)
    # owner publishes a public template
    await client.post("/api/v1/templates/capture", headers=headers,
                      json={"kind": "project", "source_id": pid,
                            "name": "Public scaffold", "visibility": "public"})
    # and a private one
    await client.post("/api/v1/templates/capture", headers=headers,
                      json={"kind": "project", "source_id": pid,
                            "name": "Private scaffold", "visibility": "workspace"})

    # gallery needs no auth
    r = await client.get("/api/v1/templates/gallery")
    assert r.status_code == 200
    names = {t["name"] for t in r.json()}
    assert "Public scaffold" in names
    assert "Private scaffold" not in names


@pytest.mark.asyncio
async def test_workspace_template_isolated_from_other_workspace(client):
    alice = await register_and_login(client, email="alice@test.dev")
    pid = await _make_project_with_content(client, alice)
    tpl = (await client.post("/api/v1/templates/capture", headers=alice,
                             json={"kind": "project", "source_id": pid,
                                   "name": "Alice private",
                                   "visibility": "workspace"})).json()

    bob = await register_and_login(client, email="bob@test.dev")  # own workspace
    # bob can't see or use alice's workspace-scoped template
    assert (await client.get(f"/api/v1/templates/{tpl['id']}", headers=bob)).status_code == 404
    assert (await client.post(f"/api/v1/templates/{tpl['id']}/use",
                              headers=bob)).status_code == 404
    listing = (await client.get("/api/v1/templates", headers=bob)).json()
    assert all(t["name"] != "Alice private" for t in listing)


@pytest.mark.asyncio
async def test_delete_template(client):
    headers = await register_and_login(client)
    pid = await _make_project_with_content(client, headers)
    tpl = (await client.post("/api/v1/templates/capture", headers=headers,
                             json={"kind": "project", "source_id": pid,
                                   "name": "Throwaway"})).json()
    assert (await client.delete(f"/api/v1/templates/{tpl['id']}",
                                headers=headers)).status_code == 204
    assert (await client.get(f"/api/v1/templates/{tpl['id']}",
                             headers=headers)).status_code == 404
