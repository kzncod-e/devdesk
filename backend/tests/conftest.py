import uuid

import httpx
import pytest
from pymongo import AsyncMongoClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from testcontainers.mongodb import MongoDbContainer

from app.api.deps import get_html_fetcher
from app.db.mongo import ensure_mongo_indexes, get_mongo_db
from app.db.postgres import Base, get_session
from app.main import create_app

STUB_HTML = """<html><head>
<title>Stub Page</title>
<meta name="description" content="Stubbed description">
<link rel="icon" href="/stub-icon.png">
</head></html>"""


@pytest.fixture(scope="session")
def mongo_container_url():
    with MongoDbContainer("mongo:7") as m:
        yield m.get_connection_url()


@pytest.fixture
async def client(mongo_container_url):
    # in-memory SQLite keeps API tests fast; SQL specifics are covered by
    # the testcontainers integration tier. Mongo has no async fake, so the
    # API tier shares one real container with a fresh database per test.
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    mongo_client = AsyncMongoClient(mongo_container_url)
    mongo_db = mongo_client[f"test_{uuid.uuid4().hex[:12]}"]
    # ASGITransport skips lifespan, so create the $text indexes here
    await ensure_mongo_indexes(mongo_db)

    app = create_app()

    async def override_session():
        async with maker() as s:
            yield s

    async def override_mongo_db():
        yield mongo_db

    async def stub_fetch_html(url: str) -> str:
        return STUB_HTML

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_mongo_db] = override_mongo_db
    app.dependency_overrides[get_html_fetcher] = lambda: stub_fetch_html
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await mongo_client.drop_database(mongo_db.name)
    await mongo_client.close()
    await engine.dispose()


async def register_and_login(client, email="user@test.dev", password="pw123456"):
    await client.post("/api/v1/auth/register",
                      json={"email": email, "password": password, "name": "Test"})
    resp = await client.post("/api/v1/auth/login",
                             json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
