import pytest

from app.core.errors import NotFoundError
from app.services.bookmark_service import BookmarkService
from app.services.snippet_service import SnippetService


class FakeSession:
    def add(self, obj):
        pass

    async def commit(self):
        pass

    async def flush(self):
        pass


class FakeProjectRepo:
    def __init__(self, in_workspace: dict[int, int] | None = None):
        # project_id -> workspace_id
        self.in_workspace = in_workspace or {}

    async def get_for_workspace(self, project_id, workspace_id):
        return object() if self.in_workspace.get(project_id) == workspace_id else None


class FakeDocRepo:
    def __init__(self):
        self.docs = {}
        self._next = 1

    def _store(self, doc):
        doc_id = self._next
        self._next += 1
        doc["id"] = doc_id
        self.docs[doc_id] = doc
        return doc

    async def get(self, doc_id, workspace_id):
        d = self.docs.get(doc_id)
        return d if d and d["workspace_id"] == workspace_id else None

    async def list(self, *, workspace_id, limit, offset, **filters):
        return [d for d in self.docs.values() if d["workspace_id"] == workspace_id]

    async def update(self, doc_id, workspace_id, *, fields):
        d = await self.get(doc_id, workspace_id)
        if d is None:
            return None
        d.update(fields)
        return d

    async def delete(self, doc_id, workspace_id):
        if await self.get(doc_id, workspace_id) is None:
            return False
        del self.docs[doc_id]
        return True


class FakeSnippetRepo(FakeDocRepo):
    async def create(self, *, workspace_id, owner_id, title, language, code, tags,
                     notes, project_id, collection_id=None):
        return self._store({"workspace_id": workspace_id, "owner_id": owner_id,
                            "title": title, "language": language, "code": code,
                            "tags": tags, "notes": notes, "project_id": project_id,
                            "collection_id": collection_id})


class FakeBookmarkRepo(FakeDocRepo):
    def __init__(self):
        super().__init__()
        self.meta_calls = []

    async def create(self, *, workspace_id, owner_id, url, tags, project_id,
                     collection_id=None):
        return self._store({"workspace_id": workspace_id, "owner_id": owner_id,
                            "url": url, "tags": tags, "project_id": project_id,
                            "collection_id": collection_id,
                            "title": "", "description": "", "favicon": "",
                            "fetched_meta": {}})

    async def set_metadata(self, bookmark_id, *, title, description, favicon,
                           fetched_meta):
        self.meta_calls.append(bookmark_id)
        d = self.docs.get(bookmark_id)
        if d:
            d.update(title=title, description=description, favicon=favicon,
                     fetched_meta=fetched_meta)
        return d


@pytest.mark.asyncio
async def test_snippet_create_validates_project_in_workspace():
    svc = SnippetService(FakeSession(), FakeSnippetRepo(), FakeProjectRepo({7: 1}))
    s = await svc.create(workspace_id=1, owner_id=1, title="T", language="py", code="x",
                         tags=[], notes="", project_id=7)
    assert s["project_id"] == 7
    # project in a different workspace rejected with 404 semantics
    with pytest.raises(NotFoundError):
        await svc.create(workspace_id=2, owner_id=2, title="T", language="py", code="x",
                         tags=[], notes="", project_id=7)
    # project-less snippet always fine
    general = await svc.create(workspace_id=2, owner_id=2, title="G", language="py",
                               code="x", tags=[], notes="", project_id=None)
    assert general["project_id"] is None


@pytest.mark.asyncio
async def test_snippet_get_update_delete_workspace_scoped():
    svc = SnippetService(FakeSession(), FakeSnippetRepo(), FakeProjectRepo())
    s = await svc.create(workspace_id=1, owner_id=1, title="T", language="py", code="x",
                         tags=[], notes="", project_id=None)
    assert (await svc.get(s["id"], workspace_id=1))["title"] == "T"
    with pytest.raises(NotFoundError):
        await svc.get(s["id"], workspace_id=2)
    with pytest.raises(NotFoundError):
        await svc.update(s["id"], workspace_id=2, fields={"title": "Hax"})
    with pytest.raises(NotFoundError):
        await svc.delete(s["id"], workspace_id=2)
    await svc.delete(s["id"], workspace_id=1)
    with pytest.raises(NotFoundError):
        await svc.get(s["id"], workspace_id=1)


@pytest.mark.asyncio
async def test_snippet_update_revalidates_new_project():
    svc = SnippetService(FakeSession(), FakeSnippetRepo(), FakeProjectRepo({7: 1}))
    s = await svc.create(workspace_id=1, owner_id=1, title="T", language="py", code="x",
                         tags=[], notes="", project_id=None)
    moved = await svc.update(s["id"], workspace_id=1, fields={"project_id": 7})
    assert moved["project_id"] == 7
    with pytest.raises(NotFoundError):
        await svc.update(s["id"], workspace_id=1, fields={"project_id": 99})


# The metadata-fetch success path opens its own DB session (it runs after the
# request), so it is covered end-to-end by test_bookmarks_api rather than faked here.


@pytest.mark.asyncio
async def test_bookmark_fetch_errors_leave_doc_untouched():
    repo = FakeBookmarkRepo()

    async def broken_fetch(url: str) -> str:
        raise RuntimeError("network down")

    svc = BookmarkService(FakeSession(), repo, FakeProjectRepo(), fetch_html=broken_fetch)
    b = await svc.create(workspace_id=1, owner_id=1, url="https://example.com/x",
                         tags=[], project_id=None)
    await svc.fetch_and_store_meta(b["id"], b["url"])  # must not raise
    assert repo.docs[b["id"]]["title"] == ""
    assert repo.meta_calls == []
