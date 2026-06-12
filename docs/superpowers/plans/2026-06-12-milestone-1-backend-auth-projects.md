# DevDesk Milestone 1: Backend Skeleton + Auth + Projects CRUD — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Dockerized FastAPI backend with JWT auth (register/login/refresh/me) and owner-scoped Projects CRUD, fully tested (unit + integration + API tiers), green pipeline locally.

**Architecture:** Clean Architecture monolith — `routers → services → repositories → models/schemas`. Routers never touch the DB; services never touch HTTP. PostgreSQL via async SQLAlchemy 2.0. Tables created from metadata at startup for this milestone (Alembic migrations arrive in Milestone 2 when the schema starts evolving — YAGNI now).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (asyncpg), Pydantic v2 + pydantic-settings, passlib[bcrypt], PyJWT, pytest + pytest-asyncio + httpx, testcontainers[postgres], ruff, Docker Compose.

---

## File Structure

```
devdesk/
├── docker-compose.yml
└── backend/
    ├── Dockerfile
    ├── pyproject.toml
    ├── .env.example
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                  # app factory, lifespan, router mounting
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py            # pydantic-settings Settings
    │   │   ├── security.py          # bcrypt + JWT helpers (pure functions)
    │   │   └── errors.py            # AppError hierarchy + handlers
    │   ├── db/
    │   │   ├── __init__.py
    │   │   └── postgres.py          # engine, session factory, Base, get_session
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── user.py              # User ORM model
    │   │   └── project.py           # Project ORM model
    │   ├── schemas/
    │   │   ├── __init__.py
    │   │   ├── auth.py              # RegisterIn, LoginIn, TokenOut, UserOut
    │   │   └── project.py           # ProjectIn, ProjectPatch, ProjectOut
    │   ├── repositories/
    │   │   ├── __init__.py
    │   │   ├── user_repo.py         # UserRepository
    │   │   └── project_repo.py      # ProjectRepository
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── auth_service.py      # AuthService
    │   │   └── project_service.py   # ProjectService (owner scoping lives here)
    │   ├── api/
    │   │   ├── __init__.py
    │   │   └── deps.py              # DI: get_current_user, service providers
    │   └── routers/
    │       ├── __init__.py
    │       ├── auth.py
    │       └── projects.py
    └── tests/
        ├── conftest.py
        ├── unit/
        │   ├── test_security.py
        │   ├── test_auth_service.py
        │   └── test_project_service.py
        ├── integration/
        │   └── test_repositories.py
        └── api/
            ├── test_auth_api.py
            └── test_projects_api.py
```

---

### Task 1: Project scaffold + tooling + health endpoint

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`, `backend/app/main.py`
- Create: `backend/tests/conftest.py` (minimal for now)
- Test: `backend/tests/api/test_health.py`

- [ ] **Step 1: Create `backend/pyproject.toml`**

```toml
[project]
name = "devdesk-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "passlib[bcrypt]>=1.7",
    "pyjwt>=2.8",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "testcontainers[postgres]>=4.5",
    "aiosqlite>=0.20",
    "ruff>=0.4",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 2: Install dependencies**

Run from `backend/`: `python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"`
Expected: install completes without errors.

- [ ] **Step 3: Write the failing test** — `backend/tests/api/test_health.py`

```python
import httpx
import pytest

from app.main import create_app


@pytest.mark.asyncio
async def test_health_returns_ok():
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

Also create empty `backend/tests/conftest.py` and empty `__init__.py` files in `app/` packages as listed in File Structure.

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/api/test_health.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'` or `ImportError: cannot import name 'create_app'`.

- [ ] **Step 5: Write minimal implementation** — `backend/app/main.py`

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="DevDesk API", docs_url="/docs", openapi_url="/api/v1/openapi.json")

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/api/test_health.py -v` — Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat(backend): scaffold FastAPI app with health endpoint"
```

---

### Task 2: Settings module

**Files:**
- Create: `backend/app/core/config.py`, `backend/.env.example`
- Test: `backend/tests/unit/test_config.py`

- [ ] **Step 1: Write the failing test** — `backend/tests/unit/test_config.py`

```python
from app.core.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://u:p@host:5432/db"
    assert s.jwt_secret == "test-secret"
    assert s.access_token_minutes == 15
    assert s.refresh_token_days == 7
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_config.py -v` — Expected: FAIL (module not found).

- [ ] **Step 3: Implement** — `backend/app/core/config.py`

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://devdesk:devdesk@localhost:5432/devdesk"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

And `backend/.env.example`:

```
DATABASE_URL=postgresql+asyncpg://devdesk:devdesk@localhost:5432/devdesk
JWT_SECRET=change-me-in-production
CORS_ORIGINS=["http://localhost:3000"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_config.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/.env.example backend/tests/unit/test_config.py
git commit -m "feat(backend): pydantic settings module"
```

---

### Task 3: Security helpers (bcrypt + JWT)

**Files:**
- Create: `backend/app/core/security.py`
- Test: `backend/tests/unit/test_security.py`

- [ ] **Step 1: Write the failing tests** — `backend/tests/unit/test_security.py`

```python
import pytest

from app.core.security import (
    create_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("s3cret!")
    assert h != "s3cret!"
    assert verify_password("s3cret!", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_roundtrip():
    token = create_token(subject="42", token_type="access", secret="k", minutes=15)
    payload = decode_token(token, secret="k")
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_jwt_rejects_bad_secret():
    token = create_token(subject="42", token_type="access", secret="k", minutes=15)
    with pytest.raises(Exception):
        decode_token(token, secret="other")


def test_jwt_rejects_expired():
    token = create_token(subject="42", token_type="access", secret="k", minutes=-1)
    with pytest.raises(Exception):
        decode_token(token, secret="k")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_security.py -v` — Expected: FAIL (import error).

- [ ] **Step 3: Implement** — `backend/app/core/security.py`

```python
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_token(*, subject: str, token_type: str, secret: str, minutes: int,
                 algorithm: str = "HS256") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str, *, secret: str, algorithm: str = "HS256") -> dict:
    return jwt.decode(token, secret, algorithms=[algorithm])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_security.py -v` — Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/tests/unit/test_security.py
git commit -m "feat(backend): bcrypt and JWT security helpers"
```

---

### Task 4: Database setup + ORM models

**Files:**
- Create: `backend/app/db/postgres.py`, `backend/app/models/user.py`, `backend/app/models/project.py`
- Modify: `backend/app/main.py` (lifespan creates tables)

- [ ] **Step 1: Implement `backend/app/db/postgres.py`** (infrastructure — verified by integration tests in Task 5)

```python
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str | None = None):
    return create_async_engine(url or get_settings().database_url, echo=False)


engine = make_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
```

- [ ] **Step 2: Implement `backend/app/models/user.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 3: Implement `backend/app/models/project.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active|archived
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 4: Wire table creation into the app lifespan** — replace `backend/app/main.py` with:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.postgres import Base, engine
import app.models.user  # noqa: F401  (register models on Base.metadata)
import app.models.project  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="DevDesk API",
        docs_url="/docs",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Run existing tests to verify nothing broke**

Run: `pytest tests/unit tests/api/test_health.py -v`
Expected: all PASS (health test uses ASGITransport without lifespan, so no DB needed).

- [ ] **Step 6: Commit**

```bash
git add backend/app/db backend/app/models backend/app/main.py
git commit -m "feat(backend): async SQLAlchemy setup with User and Project models"
```

---

### Task 5: Repositories + integration tests (testcontainers)

**Files:**
- Create: `backend/app/repositories/user_repo.py`, `backend/app/repositories/project_repo.py`
- Test: `backend/tests/integration/test_repositories.py`

- [ ] **Step 1: Write the failing integration tests** — `backend/tests/integration/test_repositories.py`

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration -v` (requires local Docker running)
Expected: FAIL with import errors for the repositories.

- [ ] **Step 3: Implement `backend/app/repositories/user_repo.py`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, email: str, password_hash: str, name: str) -> User:
        user = User(email=email, password_hash=password_hash, name=name)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        res = await self.session.execute(select(User).where(User.email == email))
        return res.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)
```

- [ ] **Step 4: Implement `backend/app/repositories/project_repo.py`**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, owner_id: int, name: str, description: str = "",
                     color: str = "#6366f1") -> Project:
        project = Project(owner_id=owner_id, name=name, description=description, color=color)
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def list_for_owner(self, owner_id: int, *, limit: int, offset: int) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_for_owner(self, project_id: int, owner_id: int) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update(self, project: Project, **fields) -> Project:
        for key, value in fields.items():
            if value is not None:
                setattr(project, key, value)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.commit()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/integration -v` — Expected: 2 PASS (first run pulls the postgres image; allow a minute).

- [ ] **Step 6: Commit**

```bash
git add backend/app/repositories backend/tests/integration
git commit -m "feat(backend): user and project repositories with testcontainers integration tests"
```

---

### Task 6: Error types + AuthService (unit-tested with fake repo)

**Files:**
- Create: `backend/app/core/errors.py`, `backend/app/services/auth_service.py`
- Test: `backend/tests/unit/test_auth_service.py`

- [ ] **Step 1: Implement `backend/app/core/errors.py`** (tiny, no test of its own — exercised everywhere)

```python
class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
```

- [ ] **Step 2: Write the failing tests** — `backend/tests/unit/test_auth_service.py`

```python
import pytest

from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import hash_password
from app.services.auth_service import AuthService


class FakeUserRepo:
    def __init__(self):
        self.users = {}
        self._next = 1

    async def create(self, *, email, password_hash, name):
        user = type("U", (), {"id": self._next, "email": email,
                              "password_hash": password_hash, "name": name})()
        self.users[email] = user
        self._next += 1
        return user

    async def get_by_email(self, email):
        return self.users.get(email)

    async def get_by_id(self, user_id):
        return next((u for u in self.users.values() if u.id == user_id), None)


def make_service():
    return AuthService(FakeUserRepo(), jwt_secret="test", access_minutes=15,
                       refresh_minutes=60 * 24 * 7)


@pytest.mark.asyncio
async def test_register_then_login_returns_tokens():
    svc = make_service()
    user = await svc.register(email="a@b.c", password="pw123456", name="A")
    assert user.id == 1
    tokens = await svc.login(email="a@b.c", password="pw123456")
    assert tokens.access_token and tokens.refresh_token


@pytest.mark.asyncio
async def test_register_duplicate_email_raises_conflict():
    svc = make_service()
    await svc.register(email="a@b.c", password="pw123456", name="A")
    with pytest.raises(ConflictError):
        await svc.register(email="a@b.c", password="other123", name="B")


@pytest.mark.asyncio
async def test_login_wrong_password_raises_unauthorized():
    svc = make_service()
    await svc.register(email="a@b.c", password="pw123456", name="A")
    with pytest.raises(UnauthorizedError):
        await svc.login(email="a@b.c", password="wrong")


@pytest.mark.asyncio
async def test_refresh_rejects_access_token():
    svc = make_service()
    await svc.register(email="a@b.c", password="pw123456", name="A")
    tokens = await svc.login(email="a@b.c", password="pw123456")
    with pytest.raises(UnauthorizedError):
        await svc.refresh(tokens.access_token)  # wrong token type
    new_tokens = await svc.refresh(tokens.refresh_token)
    assert new_tokens.access_token
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/unit/test_auth_service.py -v` — Expected: FAIL (no AuthService).

- [ ] **Step 4: Implement `backend/app/services/auth_service.py`**

```python
from dataclasses import dataclass

import jwt as pyjwt

from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import create_token, decode_token, hash_password, verify_password


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthService:
    def __init__(self, user_repo, *, jwt_secret: str, access_minutes: int,
                 refresh_minutes: int) -> None:
        self.user_repo = user_repo
        self.jwt_secret = jwt_secret
        self.access_minutes = access_minutes
        self.refresh_minutes = refresh_minutes

    async def register(self, *, email: str, password: str, name: str):
        if await self.user_repo.get_by_email(email):
            raise ConflictError("Email already registered")
        return await self.user_repo.create(
            email=email, password_hash=hash_password(password), name=name
        )

    async def login(self, *, email: str, password: str) -> TokenPair:
        user = await self.user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        return self._issue(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Not a refresh token")
        return self._issue(int(payload["sub"]))

    async def get_user(self, access_token: str):
        payload = self._decode(access_token)
        if payload.get("type") != "access":
            raise UnauthorizedError("Not an access token")
        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if user is None:
            raise UnauthorizedError("User no longer exists")
        return user

    def _issue(self, user_id: int) -> TokenPair:
        return TokenPair(
            access_token=create_token(subject=str(user_id), token_type="access",
                                      secret=self.jwt_secret, minutes=self.access_minutes),
            refresh_token=create_token(subject=str(user_id), token_type="refresh",
                                       secret=self.jwt_secret, minutes=self.refresh_minutes),
        )

    def _decode(self, token: str) -> dict:
        try:
            return decode_token(token, secret=self.jwt_secret)
        except pyjwt.PyJWTError as exc:
            raise UnauthorizedError("Invalid or expired token") from exc
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_auth_service.py -v` — Expected: 4 PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/errors.py backend/app/services/auth_service.py backend/tests/unit/test_auth_service.py
git commit -m "feat(backend): auth service with register/login/refresh and error types"
```

---

### Task 7: ProjectService (owner scoping, unit-tested)

**Files:**
- Create: `backend/app/services/project_service.py`
- Test: `backend/tests/unit/test_project_service.py`

- [ ] **Step 1: Write the failing tests** — `backend/tests/unit/test_project_service.py`

```python
import pytest

from app.core.errors import NotFoundError
from app.services.project_service import ProjectService


class FakeProjectRepo:
    def __init__(self):
        self.items = {}
        self._next = 1

    async def create(self, *, owner_id, name, description="", color="#6366f1"):
        p = type("P", (), {"id": self._next, "owner_id": owner_id, "name": name,
                           "description": description, "status": "active", "color": color})()
        self.items[p.id] = p
        self._next += 1
        return p

    async def list_for_owner(self, owner_id, *, limit, offset):
        mine = [p for p in self.items.values() if p.owner_id == owner_id]
        return mine[offset:offset + limit]

    async def get_for_owner(self, project_id, owner_id):
        p = self.items.get(project_id)
        return p if p and p.owner_id == owner_id else None

    async def update(self, project, **fields):
        for k, v in fields.items():
            if v is not None:
                setattr(project, k, v)
        return project

    async def delete(self, project):
        del self.items[project.id]


@pytest.mark.asyncio
async def test_get_other_users_project_raises_not_found():
    svc = ProjectService(FakeProjectRepo())
    p = await svc.create(owner_id=1, name="Mine")
    with pytest.raises(NotFoundError):
        await svc.get(p.id, owner_id=2)


@pytest.mark.asyncio
async def test_update_and_delete_are_owner_scoped():
    svc = ProjectService(FakeProjectRepo())
    p = await svc.create(owner_id=1, name="Mine")
    updated = await svc.update(p.id, owner_id=1, name="Renamed", status="archived")
    assert updated.name == "Renamed" and updated.status == "archived"
    with pytest.raises(NotFoundError):
        await svc.update(p.id, owner_id=2, name="Hax")
    with pytest.raises(NotFoundError):
        await svc.delete(p.id, owner_id=2)
    await svc.delete(p.id, owner_id=1)
    with pytest.raises(NotFoundError):
        await svc.get(p.id, owner_id=1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_project_service.py -v` — Expected: FAIL.

- [ ] **Step 3: Implement `backend/app/services/project_service.py`**

```python
from app.core.errors import NotFoundError


class ProjectService:
    def __init__(self, repo) -> None:
        self.repo = repo

    async def create(self, *, owner_id: int, name: str, description: str = "",
                     color: str = "#6366f1"):
        return await self.repo.create(owner_id=owner_id, name=name,
                                      description=description, color=color)

    async def list(self, owner_id: int, *, limit: int = 50, offset: int = 0):
        return await self.repo.list_for_owner(owner_id, limit=limit, offset=offset)

    async def get(self, project_id: int, owner_id: int):
        project = await self.repo.get_for_owner(project_id, owner_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    async def update(self, project_id: int, owner_id: int, **fields):
        project = await self.get(project_id, owner_id)
        return await self.repo.update(project, **fields)

    async def delete(self, project_id: int, owner_id: int) -> None:
        project = await self.get(project_id, owner_id)
        await self.repo.delete(project)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_project_service.py -v` — Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/project_service.py backend/tests/unit/test_project_service.py
git commit -m "feat(backend): owner-scoped project service"
```

---

### Task 8: Schemas, dependencies, routers, error handlers + API tests

**Files:**
- Create: `backend/app/schemas/auth.py`, `backend/app/schemas/project.py`, `backend/app/api/deps.py`, `backend/app/routers/auth.py`, `backend/app/routers/projects.py`
- Modify: `backend/app/main.py` (mount routers, exception handlers, CORS)
- Test: `backend/tests/api/test_auth_api.py`, `backend/tests/api/test_projects_api.py`, shared fixtures in `backend/tests/conftest.py`

- [ ] **Step 1: Write shared API test fixtures** — replace `backend/tests/conftest.py`:

```python
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
```

- [ ] **Step 2: Write the failing API tests** — `backend/tests/api/test_auth_api.py`:

```python
import pytest

from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_register_login_me_flow(client):
    r = await client.post("/api/v1/auth/register",
                          json={"email": "a@b.c", "password": "pw123456", "name": "A"})
    assert r.status_code == 201
    assert r.json()["email"] == "a@b.c"
    assert "password" not in r.json() and "password_hash" not in r.json()

    r = await client.post("/api/v1/auth/login",
                          json={"email": "a@b.c", "password": "pw123456"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"

    r = await client.get("/api/v1/auth/me",
                         headers={"Authorization": f"Bearer {body['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.c"


@pytest.mark.asyncio
async def test_duplicate_register_409(client):
    payload = {"email": "a@b.c", "password": "pw123456", "name": "A"}
    await client.post("/api/v1/auth/register", json=payload)
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409
    assert r.json()["code"] == "conflict"


@pytest.mark.asyncio
async def test_bad_login_401_and_me_requires_auth(client):
    r = await client.post("/api/v1/auth/login",
                          json={"email": "no@x.y", "password": "nope1234"})
    assert r.status_code == 401
    r = await client.get("/api/v1/auth/me")
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_issues_new_tokens(client):
    await client.post("/api/v1/auth/register",
                      json={"email": "a@b.c", "password": "pw123456", "name": "A"})
    login = await client.post("/api/v1/auth/login",
                              json={"email": "a@b.c", "password": "pw123456"})
    refresh_token = login.json()["refresh_token"]
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_register_validates_input(client):
    r = await client.post("/api/v1/auth/register",
                          json={"email": "not-an-email", "password": "short", "name": ""})
    assert r.status_code == 422
```

And `backend/tests/api/test_projects_api.py`:

```python
import pytest

from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_project_crud_flow(client):
    headers = await register_and_login(client)

    r = await client.post("/api/v1/projects", headers=headers,
                          json={"name": "DevDesk", "description": "workspace"})
    assert r.status_code == 201
    pid = r.json()["id"]

    r = await client.get("/api/v1/projects", headers=headers)
    assert r.status_code == 200
    assert [p["id"] for p in r.json()] == [pid]

    r = await client.patch(f"/api/v1/projects/{pid}", headers=headers,
                           json={"status": "archived"})
    assert r.status_code == 200
    assert r.json()["status"] == "archived"

    r = await client.delete(f"/api/v1/projects/{pid}", headers=headers)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/projects/{pid}", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_projects_are_owner_isolated(client):
    alice = await register_and_login(client, email="alice@test.dev")
    bob = await register_and_login(client, email="bob@test.dev")

    r = await client.post("/api/v1/projects", headers=alice, json={"name": "Secret"})
    pid = r.json()["id"]

    r = await client.get(f"/api/v1/projects/{pid}", headers=bob)
    assert r.status_code == 404  # not 403: don't leak existence
    r = await client.get("/api/v1/projects", headers=bob)
    assert r.json() == []


@pytest.mark.asyncio
async def test_projects_require_auth(client):
    r = await client.get("/api/v1/projects")
    assert r.status_code in (401, 403)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/api -v` — Expected: FAIL (404s — routes don't exist).

- [ ] **Step 4: Implement schemas** — `backend/app/schemas/auth.py`:

```python
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
```

Note: `EmailStr` needs `pip install "pydantic[email]"` — add `"pydantic[email]>=2.7"` to `pyproject.toml` dependencies (replacing the plain `pydantic` entry) and re-run `pip install -e ".[dev]"`.

And `backend/app/schemas/project.py`:

```python
from pydantic import BaseModel, ConfigDict, Field


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, pattern=r"^(active|archived)$")
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    status: str
    color: str
```

- [ ] **Step 5: Implement dependencies** — `backend/app/api/deps.py`:

```python
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.postgres import get_session
from app.repositories.project_repo import ProjectRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService

bearer = HTTPBearer(auto_error=True)


def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        UserRepository(session),
        jwt_secret=settings.jwt_secret,
        access_minutes=settings.access_token_minutes,
        refresh_minutes=settings.refresh_token_days * 24 * 60,
    )


def get_project_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectService:
    return ProjectService(ProjectRepository(session))


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth.get_user(creds.credentials)
```

- [ ] **Step 6: Implement routers** — `backend/app/routers/auth.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn,
                   auth: Annotated[AuthService, Depends(get_auth_service)]):
    return await auth.register(email=body.email, password=body.password, name=body.name)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn,
                auth: Annotated[AuthService, Depends(get_auth_service)]):
    return await auth.login(email=body.email, password=body.password)


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn,
                  auth: Annotated[AuthService, Depends(get_auth_service)]):
    return await auth.refresh(body.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[object, Depends(get_current_user)]):
    return user
```

And `backend/app/routers/projects.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_project_service
from app.schemas.project import ProjectIn, ProjectOut, ProjectPatch
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[ProjectService, Depends(get_project_service)]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectIn, user: CurrentUser, svc: Service):
    return await svc.create(owner_id=user.id, name=body.name,
                            description=body.description, color=body.color)


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: CurrentUser, svc: Service,
                        limit: int = Query(50, ge=1, le=100),
                        offset: int = Query(0, ge=0)):
    return await svc.list(user.id, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, user: CurrentUser, svc: Service):
    return await svc.get(project_id, user.id)


@router.patch("/{project_id}", response_model=ProjectOut)
async def patch_project(project_id: int, body: ProjectPatch,
                        user: CurrentUser, svc: Service):
    return await svc.update(project_id, user.id,
                            **body.model_dump(exclude_unset=True))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, user: CurrentUser, svc: Service):
    await svc.delete(project_id, user.id)
```

- [ ] **Step 7: Wire everything in `backend/app/main.py`** — replace the file:

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.postgres import Base, engine
from app.routers import auth, projects
import app.models.user  # noqa: F401
import app.models.project  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="DevDesk API",
        docs_url="/docs",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code,
                            content={"detail": exc.detail, "code": exc.code})

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(projects.router)
    return app


app = create_app()
```

- [ ] **Step 8: Run the full suite**

Run: `pytest tests/unit tests/api -v` — Expected: all PASS.
Then: `pytest tests -v` (includes integration; Docker required) — Expected: all PASS.

- [ ] **Step 9: Lint and commit**

```bash
ruff check backend/ --fix
git add backend/
git commit -m "feat(backend): auth and projects REST API with error envelope and API tests"
```

---

### Task 9: Dockerize + Compose

**Files:**
- Create: `backend/Dockerfile`, `docker-compose.yml`, `backend/.dockerignore`

- [ ] **Step 1: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml ./
RUN pip install --no-cache-dir .
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

And `backend/.dockerignore`:

```
.venv
__pycache__
tests
.pytest_cache
.ruff_cache
```

- [ ] **Step 2: Create `docker-compose.yml`** (repo root)

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: devdesk
      POSTGRES_PASSWORD: devdesk
      POSTGRES_DB: devdesk
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devdesk"]
      interval: 5s
      timeout: 3s
      retries: 10

  mongo:
    image: mongo:7
    volumes:
      - mongodata:/data/db

  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://devdesk:devdesk@postgres:5432/devdesk
      JWT_SECRET: dev-only-secret-change-me
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pgdata:
  mongodata:
```

(Mongo is included now so the compose topology is final; the API starts using it in Milestone 3.)

- [ ] **Step 3: Smoke-test the stack**

Run: `docker compose up -d --build`
Then: `curl -s http://localhost:8000/api/v1/health`
Expected: `{"status":"ok"}`

Then register a user end-to-end:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@devdesk.dev","password":"pw123456","name":"Me"}'
```

Expected: JSON with `id`, `email`, `name` and HTTP 201. Visit `http://localhost:8000/docs` and confirm OpenAPI docs render.

- [ ] **Step 4: Tear down and commit**

```bash
docker compose down
git add backend/Dockerfile backend/.dockerignore docker-compose.yml
git commit -m "feat(infra): dockerize API with compose (postgres, mongo, api)"
```

---

## Self-Review Notes

- **Spec coverage (Milestone 1 scope):** auth endpoints ✔ (Task 6/8), projects CRUD + owner scoping ✔ (Tasks 5/7/8), error envelope `{detail, code}` ✔ (Tasks 6/8), pagination ✔ (Task 8), CORS ✔ (Task 8), bcrypt + JWT with access/refresh split ✔ (Tasks 3/6), Dockerized ✔ (Task 9), three test tiers ✔ (unit Tasks 3/6/7, integration Task 5, API Task 8). `GET /projects/{id}/summary` deliberately deferred to Milestone 2 — it counts tasks/snippets/bookmarks, none of which exist yet.
- **Deviations from spec, intentional:** Alembic deferred (metadata create_all is sufficient until the schema evolves in Milestone 2); rate limiting (slowapi) and nginx security headers deferred to Milestone 5 (deployment) where nginx enters the stack; httpOnly-cookie refresh storage is a frontend concern (Milestone 2) — the API returns the token pair and the Nuxt app will store them appropriately.
- **Type consistency:** `TokenPair` fields match `TokenOut` schema; repo method names (`list_for_owner`, `get_for_owner`) consistent between fakes, tests, and implementations; `get_session` is the single DI seam overridden in tests.
