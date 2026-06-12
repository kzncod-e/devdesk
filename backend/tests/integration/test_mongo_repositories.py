import pytest
from pymongo import AsyncMongoClient
from testcontainers.mongodb import MongoDbContainer

from app.repositories.bookmark_repo import BookmarkRepository
from app.repositories.snippet_repo import SnippetRepository


@pytest.fixture(scope="module")
def mongo_url():
    with MongoDbContainer("mongo:7") as m:
        yield m.get_connection_url()


@pytest.fixture
async def db(mongo_url):
    client = AsyncMongoClient(mongo_url)
    database = client["devdesk_test"]
    await database.snippets.drop()
    await database.bookmarks.drop()
    yield database
    await client.close()


@pytest.mark.asyncio
async def test_snippet_crud_owner_scoped(db):
    repo = SnippetRepository(db)
    s = await repo.create(owner_id=1, title="Fetch wrapper", language="typescript",
                          code="export {}", tags=["nuxt", "http"], notes="", project_id=7)
    assert isinstance(s["id"], str)
    assert s["tags"] == ["nuxt", "http"] and s["project_id"] == 7

    assert (await repo.get(s["id"], owner_id=1))["title"] == "Fetch wrapper"
    assert await repo.get(s["id"], owner_id=2) is None
    assert await repo.get("not-an-objectid", owner_id=1) is None

    updated = await repo.update(s["id"], owner_id=1,
                                fields={"title": "Renamed", "tags": ["nuxt"]})
    assert updated["title"] == "Renamed" and updated["tags"] == ["nuxt"]
    assert await repo.update(s["id"], owner_id=2, fields={"title": "Hax"}) is None

    assert await repo.delete(s["id"], owner_id=2) is False
    assert await repo.delete(s["id"], owner_id=1) is True
    assert await repo.get(s["id"], owner_id=1) is None


@pytest.mark.asyncio
async def test_snippet_list_filters_and_pagination(db):
    repo = SnippetRepository(db)
    await repo.create(owner_id=1, title="A", language="python", code="x",
                      tags=["api"], notes="", project_id=1)
    await repo.create(owner_id=1, title="B", language="python", code="x",
                      tags=["cli"], notes="", project_id=None)
    await repo.create(owner_id=1, title="C", language="sql", code="x",
                      tags=["api"], notes="", project_id=1)
    await repo.create(owner_id=2, title="D", language="python", code="x",
                      tags=["api"], notes="", project_id=None)

    assert len(await repo.list(owner_id=1, limit=50, offset=0)) == 3
    assert {s["title"] for s in await repo.list(owner_id=1, language="python",
                                                limit=50, offset=0)} == {"A", "B"}
    assert {s["title"] for s in await repo.list(owner_id=1, tag="api",
                                                limit=50, offset=0)} == {"A", "C"}
    assert {s["title"] for s in await repo.list(owner_id=1, project_id=1,
                                                limit=50, offset=0)} == {"A", "C"}
    page = await repo.list(owner_id=1, limit=2, offset=2)
    assert len(page) == 1


@pytest.mark.asyncio
async def test_bookmark_create_set_metadata_and_filters(db):
    repo = BookmarkRepository(db)
    b = await repo.create(owner_id=1, url="https://nuxt.com/docs", tags=["docs"],
                          project_id=None)
    assert b["title"] == "" and b["fetched_meta"] == {} and b["favicon"] == ""

    stored = await repo.set_metadata(b["id"], title="Nuxt Docs", description="Guide",
                                     favicon="https://nuxt.com/icon.png",
                                     fetched_meta={"raw_title": "Nuxt Docs"})
    assert stored["title"] == "Nuxt Docs"
    assert stored["fetched_meta"]["raw_title"] == "Nuxt Docs"

    await repo.create(owner_id=1, url="https://b.example", tags=["api"], project_id=3)
    await repo.create(owner_id=2, url="https://c.example", tags=["docs"], project_id=None)

    assert len(await repo.list(owner_id=1, limit=50, offset=0)) == 2
    assert len(await repo.list(owner_id=1, tag="docs", limit=50, offset=0)) == 1
    assert len(await repo.list(owner_id=1, project_id=3, limit=50, offset=0)) == 1


@pytest.mark.asyncio
async def test_detach_project_and_count(db):
    snippets = SnippetRepository(db)
    bookmarks = BookmarkRepository(db)
    await snippets.create(owner_id=1, title="A", language="py", code="x",
                          tags=[], notes="", project_id=9)
    await snippets.create(owner_id=1, title="B", language="py", code="x",
                          tags=[], notes="", project_id=9)
    await bookmarks.create(owner_id=1, url="https://x.example", tags=[], project_id=9)

    assert await snippets.count_for_project(9) == 2
    assert await bookmarks.count_for_project(9) == 1

    await snippets.detach_project(9)
    await bookmarks.detach_project(9)

    assert await snippets.count_for_project(9) == 0
    remaining = await snippets.list(owner_id=1, limit=50, offset=0)
    assert all(s["project_id"] is None for s in remaining)
    assert len(remaining) == 2
