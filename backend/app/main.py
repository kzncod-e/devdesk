from contextlib import asynccontextmanager

import cloudinary
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.mongo import backfill_workspace_ids, ensure_mongo_indexes, get_client
from app.db.postgres import Base, engine
from app.routers import (
    admin, auth, bookmarks, projects, search, snippets, tasks, users, workspaces,
)
import app.models.user  # noqa: F401
import app.models.project  # noqa: F401
import app.models.task  # noqa: F401
import app.models.workspace  # noqa: F401

# Columns added after initial schema creation — safe to run repeatedly.
_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'member'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)",
    # Task assignees join table (Base.metadata.create_all also creates it, but this is
    # explicit/idempotent and keeps the ON DELETE CASCADE behaviour on existing DBs).
    """
    CREATE TABLE IF NOT EXISTS task_assignees (
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        PRIMARY KEY (task_id, user_id)
    )
    """,
    # ── Tenancy (increment 1): workspace_id columns on existing content ──
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workspace_id INTEGER",
    "CREATE INDEX IF NOT EXISTS ix_projects_workspace_id ON projects(workspace_id)",
    "CREATE INDEX IF NOT EXISTS ix_tasks_workspace_id ON tasks(workspace_id)",
    # ── Backfill: give every existing user a personal owner workspace, then
    #    attach their projects/tasks to it. All statements are idempotent. ──
    """
    INSERT INTO workspaces (name, slug, plan, created_by, created_at)
    SELECT u.name || ' Workspace', 'ws-' || u.id, 'free', u.id, now()
    FROM users u
    WHERE NOT EXISTS (SELECT 1 FROM memberships m WHERE m.user_id = u.id)
      AND NOT EXISTS (SELECT 1 FROM workspaces w WHERE w.slug = 'ws-' || u.id)
    """,
    """
    INSERT INTO memberships (workspace_id, user_id, role, status, created_at)
    SELECT w.id, w.created_by, 'owner', 'active', now()
    FROM workspaces w
    WHERE w.slug = 'ws-' || w.created_by
      AND NOT EXISTS (
        SELECT 1 FROM memberships m
        WHERE m.workspace_id = w.id AND m.user_id = w.created_by
      )
    """,
    """
    UPDATE projects p SET workspace_id = (
        SELECT m.workspace_id FROM memberships m
        WHERE m.user_id = p.owner_id AND m.role = 'owner'
        ORDER BY m.workspace_id LIMIT 1
    ) WHERE p.workspace_id IS NULL
    """,
    """
    UPDATE tasks t SET workspace_id = (
        SELECT p.workspace_id FROM projects p WHERE p.id = t.project_id
    ) WHERE t.workspace_id IS NULL
    """,
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _MIGRATIONS:
            await conn.execute(text(stmt))
        # Map each user's personal workspace, to backfill legacy Mongo docs.
        rows = (await conn.execute(
            text("SELECT created_by, id FROM workspaces WHERE slug = 'ws-' || created_by")
        )).all()
    owner_to_workspace = {row[0]: row[1] for row in rows}
    mongo_db = get_client()[get_settings().mongo_db_name]
    await ensure_mongo_indexes(mongo_db)
    if owner_to_workspace:
        await backfill_workspace_ids(mongo_db, owner_to_workspace)
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
    app.include_router(admin.router)
    app.include_router(projects.router)
    app.include_router(tasks.router)
    app.include_router(snippets.router)
    app.include_router(bookmarks.router)
    app.include_router(search.router)
    app.include_router(users.router)
    app.include_router(workspaces.router)

    return app


app = create_app()
