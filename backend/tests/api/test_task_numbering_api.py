import pytest

from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_project_key_and_task_numbering(client):
    headers = await register_and_login(client)
    proj = (await client.post("/api/v1/projects", headers=headers,
                              json={"name": "Acme Platform"})).json()
    assert proj["key"] == "AP"
    pid = proj["id"]

    a = (await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                           json={"title": "One"})).json()
    b = (await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                           json={"title": "Two"})).json()
    assert a["number"] == 1 and b["number"] == 2
    assert a["parent_task_id"] is None


@pytest.mark.asyncio
async def test_subtasks_flow_and_board_excludes_them(client):
    headers = await register_and_login(client)
    pid = (await client.post("/api/v1/projects", headers=headers,
                             json={"name": "P"})).json()["id"]
    parent = (await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                                json={"title": "Parent"})).json()

    sub = (await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                             json={"title": "Sub", "parent_task_id": parent["id"]})).json()
    assert sub["parent_task_id"] == parent["id"] and sub["number"] == 2

    subs = (await client.get(f"/api/v1/tasks/{parent['id']}/subtasks", headers=headers)).json()
    assert [s["title"] for s in subs] == ["Sub"]

    # board list shows only top-level tasks
    board = (await client.get(f"/api/v1/projects/{pid}/tasks", headers=headers)).json()
    assert [t["title"] for t in board] == ["Parent"]


@pytest.mark.asyncio
async def test_subtask_rejects_cross_project_parent(client):
    headers = await register_and_login(client)
    p1 = (await client.post("/api/v1/projects", headers=headers, json={"name": "P1"})).json()["id"]
    p2 = (await client.post("/api/v1/projects", headers=headers, json={"name": "P2"})).json()["id"]
    t1 = (await client.post(f"/api/v1/projects/{p1}/tasks", headers=headers,
                            json={"title": "T1"})).json()["id"]
    # parent in p1, creating under p2 → not found
    r = await client.post(f"/api/v1/projects/{p2}/tasks", headers=headers,
                          json={"title": "bad", "parent_task_id": t1})
    assert r.status_code == 404
