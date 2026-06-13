from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.asynchronous.database import AsyncDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ForbiddenError
from app.db.mongo import get_mongo_db
from app.db.postgres import get_session
from app.repositories.bookmark_repo import BookmarkRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.snippet_repo import SnippetRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthService
from app.services.bookmark_service import BookmarkService, FetchHtml, default_fetch_html
from app.services.project_service import ProjectService
from app.services.search_service import SearchService
from app.services.snippet_service import SnippetService
from app.services.task_service import TaskService
from app.services.user_service import UserService

bearer = HTTPBearer(auto_error=True)

Session = Annotated[AsyncSession, Depends(get_session)]
MongoDb = Annotated[AsyncDatabase, Depends(get_mongo_db)]


def get_auth_service(
    session: Session,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        UserRepository(session),
        jwt_secret=settings.jwt_secret,
        access_minutes=settings.access_token_minutes,
        refresh_minutes=settings.refresh_token_days * 24 * 60,
    )


def get_project_service(session: Session, mongo_db: MongoDb) -> ProjectService:
    return ProjectService(
        ProjectRepository(session),
        task_repo=TaskRepository(session),
        snippet_repo=SnippetRepository(mongo_db),
        bookmark_repo=BookmarkRepository(mongo_db),
    )


def get_task_service(session: Session) -> TaskService:
    return TaskService(TaskRepository(session), ProjectRepository(session))


def get_snippet_service(session: Session, mongo_db: MongoDb) -> SnippetService:
    return SnippetService(SnippetRepository(mongo_db), ProjectRepository(session))


def get_html_fetcher() -> FetchHtml:
    return default_fetch_html


def get_bookmark_service(
    session: Session,
    mongo_db: MongoDb,
    fetch_html: Annotated[FetchHtml, Depends(get_html_fetcher)],
) -> BookmarkService:
    return BookmarkService(BookmarkRepository(mongo_db), ProjectRepository(session),
                           fetch_html=fetch_html)


def get_search_service(session: Session, mongo_db: MongoDb) -> SearchService:
    return SearchService(
        ProjectRepository(session),
        TaskRepository(session),
        SnippetRepository(mongo_db),
        BookmarkRepository(mongo_db),
    )


def get_user_service(session: Session) -> UserService:
    return UserService(UserRepository(session))


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
):
    return await auth.get_user(creds.credentials)


async def get_admin_user(user=Depends(get_current_user)):
    if user.role != "admin":
        raise ForbiddenError("Admin access required")
    return user


async def get_manager_or_admin_user(user=Depends(get_current_user)):
    if user.role not in ("admin", "manager"):
        raise ForbiddenError("Manager or admin access required")
    return user
