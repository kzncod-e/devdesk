"""Tests for /notifications endpoints."""
import pytest

from app.models.notification import Notification
from app.platform.handlers import dispatch
from tests.conftest import register_and_login


async def _get_ws_id(client, headers) -> int:
    ws = await client.get("/api/v1/workspaces", headers=headers)
    return ws.json()[0]["id"]


async def _seed_notification(session_factory, *, user_id: int, workspace_id: int, read: bool = False):
    async with session_factory() as session:
        row = Notification(
            user_id=user_id,
            workspace_id=workspace_id,
            type="task.assigned",
            payload={"task_title": "Test task", "actor_name": "Alice"},
        )
        if read:
            from datetime import datetime, timezone
            row.read_at = datetime.now(timezone.utc)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row.id


@pytest.fixture
async def session_factory(db_maker):
    return db_maker


@pytest.mark.asyncio
async def test_notifications_empty(client):
    headers = await register_and_login(client)
    r = await client.get("/api/v1/notifications", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["next_cursor"] is None


@pytest.mark.asyncio
async def test_unread_count(client, session_factory):
    headers = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]
    ws_id = await _get_ws_id(client, headers)

    await _seed_notification(session_factory, user_id=user_id, workspace_id=ws_id)
    await _seed_notification(session_factory, user_id=user_id, workspace_id=ws_id, read=True)

    r = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert r.status_code == 200
    assert r.json()["count"] == 1


@pytest.mark.asyncio
async def test_mark_read_by_ids(client, session_factory):
    headers = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]
    ws_id = await _get_ws_id(client, headers)

    nid = await _seed_notification(session_factory, user_id=user_id, workspace_id=ws_id)
    r = await client.post("/api/v1/notifications/read", headers=headers, json={"ids": [nid]})
    assert r.status_code == 200
    assert r.json()["updated"] == 1

    count = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.json()["count"] == 0


@pytest.mark.asyncio
async def test_mark_all_read(client, session_factory):
    headers = await register_and_login(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]
    ws_id = await _get_ws_id(client, headers)

    await _seed_notification(session_factory, user_id=user_id, workspace_id=ws_id)
    await _seed_notification(session_factory, user_id=user_id, workspace_id=ws_id)

    r = await client.post("/api/v1/notifications/read", headers=headers, json={"all": True})
    assert r.status_code == 200
    assert r.json()["updated"] == 2


@pytest.mark.asyncio
async def test_task_assignment_creates_notification(client, session_factory):
    """Outbox handler fans out task.assignees_changed into a notification row."""
    alice = await register_and_login(client, email="alice@test.dev")
    ws_id = await _get_ws_id(client, alice)
    bob = await register_and_login(client, email="bob@test.dev")

    # invite bob
    inv = await client.post(
        f"/api/v1/workspaces/{ws_id}/invites",
        headers=alice,
        json={"email": "bob@test.dev", "role": "member"},
    )
    await client.post("/api/v1/invites/accept", headers=bob, json={"token": inv.json()["token"]})

    bob_me = await client.get("/api/v1/auth/me", headers=bob)
    bob_id = bob_me.json()["id"]

    proj = await client.post(
        "/api/v1/projects",
        headers=alice,
        json={"name": "Notify test", "description": "", "color": "#6366f1"},
    )
    project_id = proj.json()["id"]

    task = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=alice,
        json={"title": "Assigned task"},
    )
    task_id = task.json()["id"]

    await client.put(
        f"/api/v1/tasks/{task_id}/assignees",
        headers=alice,
        json={"user_ids": [bob_id]},
    )

    # Process the outbox event synchronously in test
    from app.models.outbox import OutboxEvent
    from sqlalchemy import select

    async with session_factory() as session:
        res = await session.execute(
            select(OutboxEvent).where(OutboxEvent.topic == "task.assignees_changed")
        )
        event = res.scalars().first()
        assert event is not None
        await dispatch(
            event.topic,
            event.payload,
            workspace_id=event.workspace_id,
            session=session,
        )
        await session.commit()

    bob_ws = {**bob, "X-Workspace-Id": str(ws_id)}
    notes = await client.get("/api/v1/notifications", headers=bob_ws)
    assert notes.status_code == 200
    items = notes.json()["items"]
    assert len(items) >= 1
    assert items[0]["type"] == "task.assigned"
    assert items[0]["payload"]["task_title"] == "Assigned task"
