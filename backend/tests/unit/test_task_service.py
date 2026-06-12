import pytest

from app.core.errors import NotFoundError
from app.services.task_service import TaskService


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

    async def get_for_owner(self, project_id, owner_id):
        p = self.items.get(project_id)
        return p if p and p.owner_id == owner_id else None


class FakeTaskRepo:
    def __init__(self, projects: FakeProjectRepo):
        self.projects = projects
        self.items = {}
        self._next = 1

    async def create(self, *, project_id, title, position, description="",
                     priority="medium", due_date=None):
        t = type("T", (), {"id": self._next, "project_id": project_id, "title": title,
                           "description": description, "status": "todo",
                           "priority": priority, "position": position,
                           "due_date": due_date})()
        self.items[t.id] = t
        self._next += 1
        return t

    async def list_for_project(self, project_id, *, limit, offset):
        mine = sorted((t for t in self.items.values() if t.project_id == project_id),
                      key=lambda t: t.position)
        return mine[offset:offset + limit]

    async def get_with_owner(self, task_id, owner_id):
        t = self.items.get(task_id)
        if t is None:
            return None
        p = self.projects.items.get(t.project_id)
        return t if p and p.owner_id == owner_id else None

    async def max_position(self, project_id, status):
        positions = [t.position for t in self.items.values()
                     if t.project_id == project_id and t.status == status]
        return max(positions) if positions else None

    async def count_by_status(self, project_id):
        counts = {}
        for t in self.items.values():
            if t.project_id == project_id:
                counts[t.status] = counts.get(t.status, 0) + 1
        return counts

    async def update(self, task, **fields):
        for k, v in fields.items():
            if v is not None:
                setattr(task, k, v)
        return task

    async def delete(self, task):
        del self.items[task.id]


@pytest.fixture
def env():
    projects = FakeProjectRepo()
    tasks = FakeTaskRepo(projects)
    return projects, tasks, TaskService(tasks, projects)


@pytest.mark.asyncio
async def test_create_appends_position(env):
    projects, tasks, svc = env
    p = await projects.create(owner_id=1, name="P")
    t1 = await svc.create(owner_id=1, project_id=p.id, title="A")
    t2 = await svc.create(owner_id=1, project_id=p.id, title="B")
    assert t1.position == 1024
    assert t2.position == 2048


@pytest.mark.asyncio
async def test_create_and_list_require_owned_project(env):
    projects, tasks, svc = env
    p = await projects.create(owner_id=1, name="P")
    with pytest.raises(NotFoundError):
        await svc.create(owner_id=2, project_id=p.id, title="Hax")
    with pytest.raises(NotFoundError):
        await svc.list(owner_id=2, project_id=p.id)
    await svc.create(owner_id=1, project_id=p.id, title="Ok")
    assert len(await svc.list(owner_id=1, project_id=p.id)) == 1


@pytest.mark.asyncio
async def test_update_and_delete_are_owner_scoped(env):
    projects, tasks, svc = env
    p = await projects.create(owner_id=1, name="P")
    t = await svc.create(owner_id=1, project_id=p.id, title="A")
    moved = await svc.update(t.id, owner_id=1, status="done", position=512.0)
    assert moved.status == "done" and moved.position == 512.0
    with pytest.raises(NotFoundError):
        await svc.update(t.id, owner_id=2, title="Hax")
    with pytest.raises(NotFoundError):
        await svc.delete(t.id, owner_id=2)
    await svc.delete(t.id, owner_id=1)
    with pytest.raises(NotFoundError):
        await svc.update(t.id, owner_id=1, title="gone")
