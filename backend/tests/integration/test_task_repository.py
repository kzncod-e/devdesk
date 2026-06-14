from datetime import date

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
async def fixtures(session):
    users = UserRepository(session)
    owner = await users.create(email="o@x.y", password_hash="h", name="O")
    other = await users.create(email="p@x.y", password_hash="h", name="P")
    spaces = WorkspaceRepository(session)
    ws = await spaces.create(name="W", slug="ws-w", created_by=owner.id)
    other_ws = await spaces.create(name="OW", slug="ws-ow", created_by=other.id)
    await session.commit()
    projects = ProjectRepository(session)
    project = await projects.create(workspace_id=ws.id, owner_id=owner.id, name="P1")
    return ws, other_ws, project


@pytest.mark.asyncio
async def test_create_defaults_and_list_ordered_by_position(session, fixtures):
    ws, other_ws, project = fixtures
    repo = TaskRepository(session)

    t1 = await repo.create(project_id=project.id, workspace_id=ws.id, title="First",
                           position=1024.0)
    t2 = await repo.create(project_id=project.id, workspace_id=ws.id, title="Second",
                           position=2048.0, priority="high", due_date=date(2026, 7, 1))
    assert t1.status == "todo" and t1.priority == "medium" and t1.due_date is None
    assert t2.priority == "high" and t2.due_date == date(2026, 7, 1)

    # move t2 above t1, list must follow position order
    await repo.update(t2, position=512.0)
    tasks = await repo.list_for_project(project.id, limit=50, offset=0)
    assert [t.id for t in tasks] == [t2.id, t1.id]


@pytest.mark.asyncio
async def test_get_in_workspace_scopes(session, fixtures):
    ws, other_ws, project = fixtures
    repo = TaskRepository(session)
    t = await repo.create(project_id=project.id, workspace_id=ws.id, title="Mine",
                          position=1024.0)

    assert (await repo.get_in_workspace(t.id, ws.id)).id == t.id
    assert await repo.get_in_workspace(t.id, other_ws.id) is None
    assert await repo.get_in_workspace(99999, ws.id) is None


@pytest.mark.asyncio
async def test_max_position_and_count_by_status(session, fixtures):
    ws, other_ws, project = fixtures
    repo = TaskRepository(session)

    assert await repo.max_position(project.id, "todo") is None
    await repo.create(project_id=project.id, workspace_id=ws.id, title="A", position=1024.0)
    await repo.create(project_id=project.id, workspace_id=ws.id, title="B", position=2048.0)
    done = await repo.create(project_id=project.id, workspace_id=ws.id, title="C",
                             position=1024.0)
    await repo.update(done, status="done")

    assert await repo.max_position(project.id, "todo") == 2048.0
    counts = await repo.count_by_status(project.id)
    assert counts == {"todo": 2, "done": 1}


@pytest.mark.asyncio
async def test_delete(session, fixtures):
    ws, other_ws, project = fixtures
    repo = TaskRepository(session)
    t = await repo.create(project_id=project.id, workspace_id=ws.id, title="Gone",
                          position=1024.0)
    await repo.delete(t)
    assert await repo.get_in_workspace(t.id, ws.id) is None
