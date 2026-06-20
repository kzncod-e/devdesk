import pytest

from tests.conftest import register_and_login


async def make_project(client, headers, name="Acme Platform"):
    return (await client.post("/api/v1/projects", headers=headers, json={"name": name})).json()["id"]


@pytest.mark.asyncio
async def test_default_states_seeded(client):
    headers = await register_and_login(client)
    pid = await make_project(client, headers)
    states = (await client.get(f"/api/v1/projects/{pid}/states", headers=headers)).json()
    assert [(s["name"], s["category"]) for s in states] == [
        ("Todo", "todo"), ("In Progress", "in_progress"), ("Done", "done")
    ]


@pytest.mark.asyncio
async def test_state_id_drives_status(client):
    headers = await register_and_login(client)
    pid = await make_project(client, headers)
    states = (await client.get(f"/api/v1/projects/{pid}/states", headers=headers)).json()
    todo, in_prog = states[0], states[1]

    # new task lands in the first (Todo) state, status derived
    t = (await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers,
                           json={"title": "X"})).json()
    assert t["state_id"] == todo["id"] and t["status"] == "todo"

    # custom column with in_progress category → moving there derives status
    review = (await client.post(f"/api/v1/projects/{pid}/states", headers=headers,
                                json={"name": "In Review", "category": "in_progress"})).json()
    moved = (await client.patch(f"/api/v1/tasks/{t['id']}", headers=headers,
                                json={"state_id": review["id"]})).json()
    assert moved["state_id"] == review["id"] and moved["status"] == "in_progress"
    assert review["position"] > in_prog["position"]  # appended after existing columns


@pytest.mark.asyncio
async def test_delete_state_requires_empty(client):
    headers = await register_and_login(client)
    pid = await make_project(client, headers)
    states = (await client.get(f"/api/v1/projects/{pid}/states", headers=headers)).json()
    todo = states[0]

    await client.post(f"/api/v1/projects/{pid}/tasks", headers=headers, json={"title": "stuck"})
    # Todo has a task → cannot delete
    assert (await client.delete(
        f"/api/v1/projects/{pid}/states/{todo['id']}", headers=headers)).status_code == 409
    # An empty column deletes fine
    empty = states[2]
    assert (await client.delete(
        f"/api/v1/projects/{pid}/states/{empty['id']}", headers=headers)).status_code == 204
