import pytest

from app.services.search_service import SearchService


class FakePgRepo:
    def __init__(self, items):
        self.items = items
        self.calls = []

    async def search(self, owner_id, q, *, limit):
        self.calls.append((owner_id, q, limit))
        return self.items[:limit]


class FakeMongoRepo:
    def __init__(self, items):
        self.items = items
        self.calls = []

    async def search(self, *, owner_id, q, limit):
        self.calls.append((owner_id, q, limit))
        return self.items[:limit]


@pytest.mark.asyncio
async def test_search_fans_out_and_groups():
    projects = FakePgRepo(["p1"])
    tasks = FakePgRepo(["t1", "t2"])
    snippets = FakeMongoRepo(["s1"])
    bookmarks = FakeMongoRepo([])
    svc = SearchService(projects, tasks, snippets, bookmarks)

    result = await svc.search(owner_id=42, q="nginx", limit_per_group=10)
    assert result == {"projects": ["p1"], "tasks": ["t1", "t2"],
                      "snippets": ["s1"], "bookmarks": []}
    assert projects.calls == [(42, "nginx", 10)]
    assert snippets.calls == [(42, "nginx", 10)]


@pytest.mark.asyncio
async def test_search_respects_per_group_limit():
    tasks = FakePgRepo(["t1", "t2", "t3"])
    svc = SearchService(FakePgRepo([]), tasks, FakeMongoRepo([]), FakeMongoRepo([]))
    result = await svc.search(owner_id=1, q="x", limit_per_group=2)
    assert result["tasks"] == ["t1", "t2"]
