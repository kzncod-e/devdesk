import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.db.postgres import Base
from app.repositories.project_repo import ProjectRepository
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


@pytest.mark.asyncio
async def test_user_create_and_get_by_email(session):
    repo = UserRepository(session)
    user = await repo.create(email="a@b.c", password_hash="h", name="A")
    assert user.id is not None
    found = await repo.get_by_email("a@b.c")
    assert found is not None and found.id == user.id
    assert await repo.get_by_email("nope@x.y") is None


@pytest.mark.asyncio
async def test_project_crud_scoped_by_owner(session):
    users = UserRepository(session)
    owner = await users.create(email="o@x.y", password_hash="h", name="O")
    other = await users.create(email="p@x.y", password_hash="h", name="P")

    repo = ProjectRepository(session)
    p = await repo.create(owner_id=owner.id, name="DevDesk", description="", color="#fff")
    assert p.status == "active"

    mine = await repo.list_for_owner(owner.id, limit=10, offset=0)
    theirs = await repo.list_for_owner(other.id, limit=10, offset=0)
    assert [x.id for x in mine] == [p.id]
    assert theirs == []

    got = await repo.get_for_owner(p.id, owner.id)
    assert got is not None
    assert await repo.get_for_owner(p.id, other.id) is None

    updated = await repo.update(p, name="DevDesk 2", status="archived")
    assert updated.name == "DevDesk 2" and updated.status == "archived"

    await repo.delete(p)
    assert await repo.get_for_owner(p.id, owner.id) is None
