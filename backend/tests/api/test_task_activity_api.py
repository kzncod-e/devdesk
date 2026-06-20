import pytest

from tests.conftest import register_and_login


async def make_task(client, headers):
    pid = (await client.post("/api/v1/projects", headers=headers, json={"name": "P"})).json()["id"]
    return (await client.post(
        f"/api/v1/projects/{pid}/tasks", headers=headers, json={"title": "T"})).json()["id"]


@pytest.mark.asyncio
async def test_task_activity_endpoint_shape(client):
    headers = await register_and_login(client)
    tid = await make_task(client, headers)
    r = await client.get(f"/api/v1/tasks/{tid}/activity", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["items"], list) and "next_cursor" in body


@pytest.mark.asyncio
async def test_task_activity_requires_auth(client):
    headers = await register_and_login(client)
    tid = await make_task(client, headers)
    assert (await client.get(f"/api/v1/tasks/{tid}/activity")).status_code in (401, 403)
