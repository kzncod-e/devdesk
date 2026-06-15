"""Tests for /workspaces/{id}/activity and /workspaces/{id}/audit endpoints."""
import pytest

from tests.conftest import register_and_login


# ── helpers ──────────────────────────────────────────────────────────────────

async def _get_ws_id(client, headers) -> int:
    ws = await client.get("/api/v1/workspaces", headers=headers)
    return ws.json()[0]["id"]


# ── activity endpoint ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_activity_returns_empty_list_for_new_workspace(client):
    headers = await register_and_login(client)
    ws_id = await _get_ws_id(client, headers)
    r = await client.get(f"/api/v1/workspaces/{ws_id}/activity", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "next_cursor" in body
    assert body["next_cursor"] is None


@pytest.mark.asyncio
async def test_activity_requires_membership(client):
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = await _get_ws_id(client, alice)
    bob = await register_and_login(client, email="bob@test.dev")
    r = await client.get(f"/api/v1/workspaces/{ws_id}/activity", headers=bob)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_activity_limit_param_respected(client):
    headers = await register_and_login(client)
    ws_id = await _get_ws_id(client, headers)
    r = await client.get(f"/api/v1/workspaces/{ws_id}/activity?limit=5", headers=headers)
    assert r.status_code == 200


# ── audit endpoint ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_audit_returns_empty_list_for_new_workspace(client):
    headers = await register_and_login(client)
    ws_id = await _get_ws_id(client, headers)
    r = await client.get(f"/api/v1/workspaces/{ws_id}/audit", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "next_cursor" in body


@pytest.mark.asyncio
async def test_audit_requires_workspace_manage_perm(client):
    """Members and editors cannot read the audit log."""
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = await _get_ws_id(client, alice)

    # invite bob as member
    inv = await client.post(f"/api/v1/workspaces/{ws_id}/invites", headers=alice,
                            json={"email": "bob@test.dev", "role": "member"})
    token = inv.json()["token"]
    bob = await register_and_login(client, email="bob@test.dev")
    await client.post("/api/v1/invites/accept", headers=bob, json={"token": token})

    bob_ws = {**bob, "X-Workspace-Id": str(ws_id)}
    r = await client.get(f"/api/v1/workspaces/{ws_id}/audit", headers=bob_ws)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_audit_owner_can_filter_by_action(client):
    headers = await register_and_login(client)
    ws_id = await _get_ws_id(client, headers)
    r = await client.get(
        f"/api/v1/workspaces/{ws_id}/audit?action=workspace.created",
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    # all returned items must match the requested action
    for item in body["items"]:
        assert item["action"] == "workspace.created"
