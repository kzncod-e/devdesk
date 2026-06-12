import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.db.postgres import Base
from app.repositories.project_repo import ProjectRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository


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
async def users(session):
    repo = UserRepository(session)
    alice = await repo.create(email="a@x.y", password_hash="h", name="A")
    bob = await repo.create(email="b@x.y", password_hash="h", name="B")
    return alice, bob


@pytest.mark.asyncio
async def test_project_search_stems_and_scopes(session, users):
    alice, bob = users
    projects = ProjectRepository(session)
    p1 = await projects.create(owner_id=alice.id, name="Deploy pipeline",
                               description="CI and VPS deployment work")
    await projects.create(owner_id=alice.id, name="Cooking blog", description="recipes")
    await projects.create(owner_id=bob.id, name="Deploy tooling", description="bob's")

    hits = await projects.search(alice.id, "deploying", limit=10)
    assert [p.id for p in hits] == [p1.id]  # stemming + owner scoping
    assert await projects.search(alice.id, "kubernetes", limit=10) == []


@pytest.mark.asyncio
async def test_task_search_matches_title_and_description(session, users):
    alice, bob = users
    projects = ProjectRepository(session)
    tasks = TaskRepository(session)
    ap = await projects.create(owner_id=alice.id, name="P")
    bp = await projects.create(owner_id=bob.id, name="P")

    t1 = await tasks.create(project_id=ap.id, title="Configure nginx", position=1024.0)
    t2 = await tasks.create(project_id=ap.id, title="Write docs",
                            description="document the nginx setup", position=2048.0)
    await tasks.create(project_id=ap.id, title="Unrelated", position=3072.0)
    await tasks.create(project_id=bp.id, title="nginx for bob", position=1024.0)

    hits = await tasks.search(alice.id, "nginx", limit=10)
    assert {t.id for t in hits} == {t1.id, t2.id}
    assert await tasks.search(bob.id, "docs", limit=10) == []
