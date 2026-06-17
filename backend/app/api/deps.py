from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.context import current_actor_id
from app.core.errors import ForbiddenError
from app.db.postgres import SessionLocal, get_session
from app.repositories.bookmark_repo import BookmarkRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.snippet_repo import SnippetRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.template_repo import TemplateRepository
from app.repositories.user_repo import UserRepository
from app.repositories.workspace_repo import (
    InviteRepository,
    MembershipRepository,
    WorkspaceRepository,
)
from app.services.auth_service import AuthService
from app.services.bookmark_service import BookmarkService, FetchHtml, default_fetch_html
from app.services.project_service import ProjectService
from app.services.search_service import SearchService
from app.services.snippet_service import SnippetService
from app.services.task_service import TaskService
from app.services.template_service import TemplateService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

bearer = HTTPBearer(auto_error=True)

Session = Annotated[AsyncSession, Depends(get_session)]


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Session factory for work that outlives the request (e.g. background
    metadata fetches). Overridden in tests to the test engine's maker."""
    return SessionLocal


Maker = Annotated[async_sessionmaker[AsyncSession], Depends(get_sessionmaker)]


def get_auth_service(
    session: Session,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        UserRepository(session),
        jwt_secret=settings.jwt_secret,
        access_minutes=settings.access_token_minutes,
        refresh_minutes=settings.refresh_token_days * 24 * 60,
        session=session,
        workspace_repo=WorkspaceRepository(session),
        membership_repo=MembershipRepository(session),
    )


def get_project_service(session: Session) -> ProjectService:
    return ProjectService(
        session,
        ProjectRepository(session),
        task_repo=TaskRepository(session),
        snippet_repo=SnippetRepository(session),
        bookmark_repo=BookmarkRepository(session),
    )


def get_task_service(session: Session) -> TaskService:
    return TaskService(
        session, TaskRepository(session), ProjectRepository(session), UserRepository(session)
    )


def get_snippet_service(session: Session) -> SnippetService:
    return SnippetService(session, SnippetRepository(session), ProjectRepository(session))


def get_html_fetcher() -> FetchHtml:
    return default_fetch_html


def get_bookmark_service(
    session: Session,
    maker: Maker,
    fetch_html: Annotated[FetchHtml, Depends(get_html_fetcher)],
) -> BookmarkService:
    return BookmarkService(session, BookmarkRepository(session), ProjectRepository(session),
                           fetch_html=fetch_html, session_factory=maker)


def get_search_service(session: Session) -> SearchService:
    return SearchService(
        ProjectRepository(session),
        TaskRepository(session),
        SnippetRepository(session),
        BookmarkRepository(session),
    )


def get_template_service(session: Session) -> TemplateService:
    return TemplateService(
        session,
        TemplateRepository(session),
        ProjectRepository(session),
        TaskRepository(session),
        SnippetRepository(session),
    )


def get_user_service(session: Session) -> UserService:
    return UserService(UserRepository(session))


def get_workspace_service(session: Session) -> WorkspaceService:
    return WorkspaceService(
        session,
        WorkspaceRepository(session),
        MembershipRepository(session),
        InviteRepository(session),
        UserRepository(session),
    )


async def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
):
    user = await auth.get_user(creds.credentials)
    current_actor_id.set(user.id)
    return user


async def get_admin_user(user=Depends(get_current_user)):
    if user.role != "admin":
        raise ForbiddenError("Admin access required")
    return user


async def get_manager_or_admin_user(user=Depends(get_current_user)):
    if user.role not in ("admin", "manager"):
        raise ForbiddenError("Manager or admin access required")
    return user
