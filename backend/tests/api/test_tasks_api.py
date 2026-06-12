import pytest

from tests.conftest import register_and_login


async def make_project(client, headers, name="P"):
    r = await client.post("/api/v1/projects", headers=headers, json={"name": name})
    return r.json()["id"]


@pytest.mark.asyncio
async def test_task_crud_flow(client):
    headers = await register_and_login(client)
    pid = await make_project(client, headers)

    r = await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                          json={"title": "First", "priority": "high",
                                "due_date": "2026-07-01"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "todo" and body["priority"] == "high"
    assert body["position"] == 1024
    tid = body["id"]

    r = await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                          json={"title": "Second"})
    assert r.json()["position"] == 2048

    r = await client.get(f"/api/v1/projects/{pid}/tasks", headers=headers)
    assert r.status_code == 200
    assert [t["title"] for t in r.json()] == ["First", "Second"]

    # board move: change status and position
    r = await client.patch(f"/api/v1/tasks/{tid}", headers=headers,
                           json={"status": "in_progress", "position": 4096})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress" and r.json()["position"] == 4096

    r = await client.delete(f"/api/v1/tasks/{tid}", headers=headers)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/projects/{pid}/tasks", headers=headers)
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_tasks_are_owner_isolated(client):
    alice = await register_and_login(client, email="alice@test.dev")
    bob = await register_and_login(client, email="bob@test.dev")
    pid = await make_project(client, alice)
    r = await client.post(f"/api/v1/projects/{pid}/tasks", headers=alice,
                          json={"title": "Secret"})
    tid = r.json()["id"]

    assert (await client.get(f"/api/v1/projects/{pid}/tasks", headers=bob)).status_code == 404
    assert (await client.post(f"/api/v1/projects/{pid}/tasks", headers=bob,
                              json={"title": "Hax"})).status_code == 404
    assert (await client.patch(f"/api/v1/tasks/{tid}", headers=bob,
                               json={"title": "Hax"})).status_code == 404
    assert (await client.delete(f"/api/v1/tasks/{tid}", headers=bob)).status_code == 404


@pytest.mark.asyncio
async def test_tasks_require_auth_and_validate(client):
    headers = await register_and_login(client)
    pid = await make_project(client, headers)

    assert (await client.get(f"/api/v1/projects/{pid}/tasks")).status_code in (401, 403)

    r = await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                          json={"title": "", "priority": "urgent"})
    assert r.status_code == 422
    r = await client.patch("/api/v1/tasks/1", headers=headers,
                           json={"status": "blocked"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_project_summary_counts(client):
    headers = await register_and_login(client)
    pid = await make_project(client, headers)

    for title in ("A", "B"):
        await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                          json={"title": title})
    r = await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                          json={"title": "C"})
    await client.patch(f"/api/v1/tasks/{r.json()['id']}", headers=headers,
                       json={"status": "done"})

    r = await client.get(f"/api/v1/projects/{pid}/summary", headers=headers)
    assert r.status_code == 200
    assert r.json() == {
        "tasks": {"todo": 2, "in_progress": 0, "done": 1, "total": 3},
        "snippets": 0,
        "bookmarks": 0,
    }

    bob = await register_and_login(client, email="bob@test.dev")
    assert (await client.get(f"/api/v1/projects/{pid}/summary", headers=bob)).status_code == 404
