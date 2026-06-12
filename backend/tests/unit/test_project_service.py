import pytest

from app.core.errors import NotFoundError
from app.services.project_service import ProjectService


class FakeProjectRepo:
    def __init__(self):
        self.items = {}
        self._next = 1

    async def create(self, *, owner_id, name, description="", color="#6366f1"):
        p = type("P", (), {"id": self._next, "owner_id": owner_id, "name": name,
                           "description": description, "status": "active", "color": color})()
        self.items[p.id] = p
        self._next += 1
        return p

    async def list_for_owner(self, owner_id, *, limit, offset):
        mine = [p for p in self.items.values() if p.owner_id == owner_id]
        return mine[offset:offset + limit]

    async def get_for_owner(self, project_id, owner_id):
        p = self.items.get(project_id)
        return p if p and p.owner_id == owner_id else None

    async def update(self, project, **fields):
        for k, v in fields.items():
            if v is not None:
                setattr(project, k, v)
        return project

    async def delete(self, project):
        del self.items[project.id]


class FakeTaskCounts:
    def __init__(self, counts):
        self._counts = counts

    async def count_by_status(self, project_id):
        return self._counts


@pytest.mark.asyncio
async def test_summary_counts_tasks_by_status():
    svc = ProjectService(FakeProjectRepo(),
                         task_repo=FakeTaskCounts({"todo": 2, "done": 1}))
    p = await svc.create(owner_id=1, name="Mine")
    summary = await svc.summary(p.id, owner_id=1)
    assert summary == {
        "tasks": {"todo": 2, "in_progress": 0, "done": 1, "total": 3},
        "snippets": 0,
        "bookmarks": 0,
    }
    with pytest.raises(NotFoundError):
        await svc.summary(p.id, owner_id=2)


@pytest.mark.asyncio
async def test_get_other_users_project_raises_not_found():
    svc = ProjectService(FakeProjectRepo())
    p = await svc.create(owner_id=1, name="Mine")
    with pytest.raises(NotFoundError):
        await svc.get(p.id, owner_id=2)


@pytest.mark.asyncio
async def test_update_and_delete_are_owner_scoped():
    svc = ProjectService(FakeProjectRepo())
    p = await svc.create(owner_id=1, name="Mine")
    updated = await svc.update(p.id, owner_id=1, name="Renamed", status="archived")
    assert updated.name == "Renamed" and updated.status == "archived"
    with pytest.raises(NotFoundError):
        await svc.update(p.id, owner_id=2, name="Hax")
    with pytest.raises(NotFoundError):
        await svc.delete(p.id, owner_id=2)
    await svc.delete(p.id, owner_id=1)
    with pytest.raises(NotFoundError):
        await svc.get(p.id, owner_id=1)
