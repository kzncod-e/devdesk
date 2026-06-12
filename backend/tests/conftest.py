import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.postgres import Base, get_session
from app.main import create_app


@pytest.fixture
async def client():
    # in-memory SQLite keeps API tests fast; SQL specifics are covered by
    # the testcontainers integration tier
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    app = create_app()

    async def override_session():
        async with maker() as s:
            yield s

    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await engine.dispose()


async def register_and_login(client, email="user@test.dev", password="pw123456"):
    await client.post("/api/v1/auth/register",
                      json={"email": email, "password": password, "name": "Test"})
    resp = await client.post("/api/v1/auth/login",
                             json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
