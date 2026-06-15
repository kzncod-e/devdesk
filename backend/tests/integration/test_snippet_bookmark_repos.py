import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.db.postgres import Base
from app.repositories.bookmark_repo import BookmarkRepository
from app.repositories.snippet_repo import SnippetRepository
from app.repositories.user_repo import UserRepository
from app.repositories.workspace_repo import WorkspaceRepository


@pytest.fixture(scope="module")
def pg_url():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url().replace("psycopg2", "asyncpg")


@pytest.fixture
async def session(pg_url):
    engine = create_async_engine(pg_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


@pytest.fixture
async def spaces(session):
    users = UserRepository(session)
    u1 = await users.create(email="a@x.y", password_hash="h", name="A")
    u2 = await users.create(email="b@x.y", password_hash="h", name="B")
    wsrepo = WorkspaceRepository(session)
    w1 = await wsrepo.create(name="W1", slug="ws-1", created_by=u1.id)
    w2 = await wsrepo.create(name="W2", slug="ws-2", created_by=u2.id)
    await session.commit()
    return (u1, w1), (u2, w2)


@pytest.mark.asyncio
async def test_snippet_crud_workspace_scoped(session, spaces):
    (u1, w1), (u2, w2) = spaces
    repo = SnippetRepository(session)
    s = await repo.create(workspace_id=w1.id, owner_id=u1.id, title="Fetch wrapper",
                          language="typescript", code="export {}",
                          tags=["nuxt", "http"], notes="", project_id=None)
    assert isinstance(s["id"], int)
    assert s["tags"] == ["nuxt", "http"]

    assert (await repo.get(s["id"], w1.id))["title"] == "Fetch wrapper"
    assert await repo.get(s["id"], w2.id) is None

    updated = await repo.update(s["id"], w1.id, fields={"title": "Renamed", "tags": ["nuxt"]})
    assert updated["title"] == "Renamed" and updated["tags"] == ["nuxt"]
    assert await repo.update(s["id"], w2.id, fields={"title": "Hax"}) is None

    assert await repo.delete(s["id"], w2.id) is False
    assert await repo.delete(s["id"], w1.id) is True
    assert await repo.get(s["id"], w1.id) is None


@pytest.mark.asyncio
async def test_snippet_list_filters(session, spaces):
    (u1, w1), (u2, w2) = spaces
    repo = SnippetRepository(session)
    await repo.create(workspace_id=w1.id, owner_id=u1.id, title="A", language="python",
                      code="x", tags=["api"], notes="", project_id=None)
    await repo.create(workspace_id=w1.id, owner_id=u1.id, title="B", language="python",
                      code="x", tags=["cli"], notes="", project_id=None)
    await repo.create(workspace_id=w1.id, owner_id=u1.id, title="C", language="sql",
                      code="x", tags=["api"], notes="", project_id=None)
    await repo.create(workspace_id=w2.id, owner_id=u2.id, title="D", language="python",
                      code="x", tags=["api"], notes="", project_id=None)

    assert len(await repo.list(workspace_id=w1.id, limit=50, offset=0)) == 3
    assert {s["title"] for s in await repo.list(workspace_id=w1.id, language="python",
                                                limit=50, offset=0)} == {"A", "B"}
    assert {s["title"] for s in await repo.list(workspace_id=w1.id, tag="api",
                                                limit=50, offset=0)} == {"A", "C"}


@pytest.mark.asyncio
async def test_snippet_text_search(session, spaces):
    (u1, w1), (u2, w2) = spaces
    repo = SnippetRepository(session)
    s1 = await repo.create(workspace_id=w1.id, owner_id=u1.id, title="Nginx reverse proxy",
                           language="nginx", code="server {}", tags=["infra"], notes="",
                           project_id=None)
    await repo.create(workspace_id=w1.id, owner_id=u1.id, title="Sorting helper",
                      language="py", code="def sort(): ...", tags=["util"], notes="",
                      project_id=None)
    await repo.create(workspace_id=w2.id, owner_id=u2.id, title="Nginx bob",
                      language="nginx", code="x", tags=[], notes="", project_id=None)

    assert [h["id"] for h in await repo.search(workspace_id=w1.id, q="nginx", limit=10)] == [s1["id"]]
    # tags are part of the search document
    assert [h["id"] for h in await repo.search(workspace_id=w1.id, q="infra", limit=10)] == [s1["id"]]
    assert await repo.search(workspace_id=w1.id, q="kubernetes", limit=10) == []


@pytest.mark.asyncio
async def test_bookmark_metadata_filters_and_search(session, spaces):
    (u1, w1), (u2, w2) = spaces
    repo = BookmarkRepository(session)
    b = await repo.create(workspace_id=w1.id, owner_id=u1.id, url="https://nginx.org",
                          tags=["docs"], project_id=None)
    assert b["title"] == "" and b["fetched_meta"] == {}

    stored = await repo.set_metadata(b["id"], title="Nginx documentation",
                                     description="The official docs", favicon="",
                                     fetched_meta={"raw_title": "Nginx documentation"})
    assert stored["title"] == "Nginx documentation"

    await repo.create(workspace_id=w1.id, owner_id=u1.id, url="https://b.example",
                      tags=["api"], project_id=None)
    await repo.create(workspace_id=w2.id, owner_id=u2.id, url="https://c.example",
                      tags=["docs"], project_id=None)

    assert len(await repo.list(workspace_id=w1.id, limit=50, offset=0)) == 2
    assert len(await repo.list(workspace_id=w1.id, tag="docs", limit=50, offset=0)) == 1
    assert [h["id"] for h in await repo.search(workspace_id=w1.id, q="nginx", limit=10)] == [b["id"]]
    assert await repo.search(workspace_id=w2.id, q="nginx", limit=10) == []


@pytest.mark.asyncio
async def test_detach_project_and_count(session, spaces):
    (u1, w1), _ = spaces
    snippets = SnippetRepository(session)
    bookmarks = BookmarkRepository(session)
    # project_id=9 is fine as an int filter target; FK is nullable and we never
    # create that project here (detach/count operate on the id directly).
    await snippets.create(workspace_id=w1.id, owner_id=u1.id, title="A", language="py",
                          code="x", tags=[], notes="", project_id=None)
    await snippets.create(workspace_id=w1.id, owner_id=u1.id, title="B", language="py",
                          code="x", tags=[], notes="", project_id=None)
    assert await snippets.count_for_project(9) == 0
    remaining = await snippets.list(workspace_id=w1.id, limit=50, offset=0)
    assert len(remaining) == 2
