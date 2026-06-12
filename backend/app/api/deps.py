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
