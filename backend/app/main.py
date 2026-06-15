from contextlib import asynccontextmanager

import cloudinary
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.routers import (
    admin, auth, bookmarks, projects, search, snippets, tasks, users, workspaces,
)
import app.models.user  # noqa: F401
import app.models.project  # noqa: F401
import app.models.task  # noqa: F401
import app.models.workspace  # noqa: F401
import app.models.snippet  # noqa: F401
import app.models.bookmark  # noqa: F401
import app.models.outbox  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is owned by Alembic now (`alembic upgrade head`, run from the
    # container entrypoint / deploy step — see Dockerfile). The app only
    # configures runtime services here.
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
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
