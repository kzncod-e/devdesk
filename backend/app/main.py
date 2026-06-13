from contextlib import asynccontextmanager

import cloudinary
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.mongo import ensure_mongo_indexes, get_client
from app.db.postgres import Base, engine
from app.routers import admin, auth, bookmarks, projects, search, snippets, tasks
import app.models.user  # noqa: F401
import app.models.project  # noqa: F401
import app.models.task  # noqa: F401

# Columns added after initial schema creation — safe to run repeatedly.
_MIGRATIONS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'member'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)",
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
    await ensure_mongo_indexes(get_client()[get_settings().mongo_db_name])
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

    return app


app = create_app()
