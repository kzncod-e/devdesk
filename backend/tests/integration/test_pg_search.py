import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.db.postgres import Base
from app.repositories.project_repo import ProjectRepository
from app.repositories.task_repo import TaskRepository
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
    alice = await users.create(email="a@x.y", password_hash="h", name="A")
    bob = await users.create(email="b@x.y", password_hash="h", name="B")
    wsrepo = WorkspaceRepository(session)
    ws_a = await wsrepo.create(name="A", slug="ws-a", created_by=alice.id)
    ws_b = await wsrepo.create(name="B", slug="ws-b", created_by=bob.id)
    await session.commit()
    return (alice, ws_a), (bob, ws_b)


@pytest.mark.asyncio
async def test_project_search_stems_and_scopes(session, spaces):
    (alice, ws_a), (bob, ws_b) = spaces
    projects = ProjectRepository(session)
    p1 = await projects.create(workspace_id=ws_a.id, owner_id=alice.id,
                               name="Deploy pipeline", description="CI and VPS deployment work")
    await projects.create(workspace_id=ws_a.id, owner_id=alice.id, name="Cooking blog",
                          description="recipes")
    await projects.create(workspace_id=ws_b.id, owner_id=bob.id, name="Deploy tooling",
                          description="bob's")

    hits = await projects.search(ws_a.id, "deploying", limit=10)
    assert [p.id for p in hits] == [p1.id]  # stemming + workspace scoping
    assert await projects.search(ws_a.id, "kubernetes", limit=10) == []


@pytest.mark.asyncio
async def test_task_search_matches_title_and_description(session, spaces):
    (alice, ws_a), (bob, ws_b) = spaces
    projects = ProjectRepository(session)
    tasks = TaskRepository(session)
    ap = await projects.create(workspace_id=ws_a.id, owner_id=alice.id, name="P")
    bp = await projects.create(workspace_id=ws_b.id, owner_id=bob.id, name="P")

    t1 = await tasks.create(project_id=ap.id, workspace_id=ws_a.id,
                            title="Configure nginx", position=1024.0)
    t2 = await tasks.create(project_id=ap.id, workspace_id=ws_a.id, title="Write docs",
                            description="document the nginx setup", position=2048.0)
    await tasks.create(project_id=ap.id, workspace_id=ws_a.id, title="Unrelated",
                       position=3072.0)
    await tasks.create(project_id=bp.id, workspace_id=ws_b.id, title="nginx for bob",
                       position=1024.0)

    hits = await tasks.search(ws_a.id, "nginx", limit=10)
    assert {t.id for t in hits} == {t1.id, t2.id}
    assert await tasks.search(ws_b.id, "docs", limit=10) == []
