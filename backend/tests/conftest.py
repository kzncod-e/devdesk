import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_html_fetcher, get_sessionmaker
from app.db.postgres import Base, get_session
from app.main import create_app

STUB_HTML = """<html><head>
<title>Stub Page</title>
<meta name="description" content="Stubbed description">
<link rel="icon" href="/stub-icon.png">
</head></html>"""


@pytest.fixture
async def client():
    # in-memory SQLite keeps API tests fast; Postgres-specific SQL (FTS, arrays)
    # is covered by the testcontainers integration tier.
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

    async def stub_fetch_html(url: str) -> str:
        return STUB_HTML

    app.dependency_overrides[get_session] = override_session
    # Background bookmark metadata fetch opens its own session from this maker.
    app.dependency_overrides[get_sessionmaker] = lambda: maker
    app.dependency_overrides[get_html_fetcher] = lambda: stub_fetch_html
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await engine.dispose()


async def register_and_login(client, email="user@test.dev", password="pw123456",
                             with_workspace=True):
    await client.post("/api/v1/auth/register",
                      json={"email": email, "password": password, "name": "Test"})
    resp = await client.post("/api/v1/auth/login",
                             json={"email": email, "password": password})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Registration auto-provisions a personal workspace; scope content calls to it.
    if with_workspace:
        ws = await client.get("/api/v1/workspaces", headers=headers)
        spaces = ws.json()
        if spaces:
            headers["X-Workspace-Id"] = str(spaces[0]["id"])
    return headers
