import pytest

from app.core.errors import NotFoundError
from app.services.project_service import ProjectService


class FakeSession:
    def add(self, obj):
        pass

    async def commit(self):
        pass

    async def flush(self):
        pass


class FakeProjectRepo:
    def __init__(self):
        self.items = {}
        self._next = 1

    async def create(self, *, workspace_id, owner_id, name, description="", color="#6366f1"):
        p = type("P", (), {"id": self._next, "workspace_id": workspace_id,
                           "owner_id": owner_id, "name": name, "description": description,
                           "status": "active", "color": color})()
        self.items[p.id] = p
        self._next += 1
        return p

    async def list_for_workspace(self, workspace_id, *, limit, offset):
        mine = [p for p in self.items.values() if p.workspace_id == workspace_id]
        return mine[offset:offset + limit]

    async def get_for_workspace(self, project_id, workspace_id):
        p = self.items.get(project_id)
        return p if p and p.workspace_id == workspace_id else None

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


class FakeDocRepo:
    def __init__(self, count=0):
        self._count = count
        self.detached = []

    async def count_for_project(self, project_id):
        return self._count

    async def detach_project(self, project_id):
        self.detached.append(project_id)


def _svc(**kwargs) -> ProjectService:
    return ProjectService(FakeSession(), FakeProjectRepo(), **kwargs)


@pytest.mark.asyncio
async def test_summary_counts_tasks_snippets_and_bookmarks():
    svc = ProjectService(FakeSession(), FakeProjectRepo(),
                         task_repo=FakeTaskCounts({"todo": 2, "done": 1}),
                         snippet_repo=FakeDocRepo(count=4),
                         bookmark_repo=FakeDocRepo(count=2))
    p = await svc.create(workspace_id=1, owner_id=1, name="Mine")
    summary = await svc.summary(p.id, workspace_id=1)
    assert summary == {
        "tasks": {"todo": 2, "in_progress": 0, "done": 1, "total": 3},
        "snippets": 4,
        "bookmarks": 2,
    }
    with pytest.raises(NotFoundError):
        await svc.summary(p.id, workspace_id=2)


@pytest.mark.asyncio
async def test_delete_detaches_mongo_docs():
    snippets = FakeDocRepo()
    bookmarks = FakeDocRepo()
    svc = ProjectService(FakeSession(), FakeProjectRepo(),
                         snippet_repo=snippets, bookmark_repo=bookmarks)
    p = await svc.create(workspace_id=1, owner_id=1, name="Mine")
    await svc.delete(p.id, workspace_id=1)
    assert snippets.detached == [p.id]
    assert bookmarks.detached == [p.id]


@pytest.mark.asyncio
async def test_get_project_in_other_workspace_raises_not_found():
    svc = _svc()
    p = await svc.create(workspace_id=1, owner_id=1, name="Mine")
    with pytest.raises(NotFoundError):
        await svc.get(p.id, workspace_id=2)


@pytest.mark.asyncio
async def test_update_and_delete_are_workspace_scoped():
    svc = _svc()
    p = await svc.create(workspace_id=1, owner_id=1, name="Mine")
    updated = await svc.update(p.id, workspace_id=1, name="Renamed", status="archived")
    assert updated.name == "Renamed" and updated.status == "archived"
    with pytest.raises(NotFoundError):
        await svc.update(p.id, workspace_id=2, name="Hax")
    with pytest.raises(NotFoundError):
        await svc.delete(p.id, workspace_id=2)
    await svc.delete(p.id, workspace_id=1)
    with pytest.raises(NotFoundError):
        await svc.get(p.id, workspace_id=1)
