from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from app.api.deps import get_auth_service, get_current_user, get_user_service
from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.schemas.auth import LoginIn, ProfilePatch, RefreshIn, RegisterIn, TokenOut, UserOut
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        "refresh_token",
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn,
                   auth: Annotated[AuthService, Depends(get_auth_service)]):
    return await auth.register(email=body.email, password=body.password, name=body.name)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn,
                auth: Annotated[AuthService, Depends(get_auth_service)],
                settings: Annotated[Settings, Depends(get_settings)],
                response: Response):
    tokens = await auth.login(email=body.email, password=body.password)
    _set_refresh_cookie(response, tokens.refresh_token, settings)
    return tokens


@router.post("/refresh", response_model=TokenOut)
async def refresh(auth: Annotated[AuthService, Depends(get_auth_service)],
                  settings: Annotated[Settings, Depends(get_settings)],
                  response: Response,
                  body: RefreshIn | None = None,
                  refresh_token: Annotated[str | None, Cookie()] = None):
    token = body.refresh_token if body else refresh_token
    if not token:
        raise UnauthorizedError("Missing refresh token")
    tokens = await auth.refresh(token)
    _set_refresh_cookie(response, tokens.refresh_token, settings)
    return tokens


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[object, Depends(get_current_user)]):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: ProfilePatch,
    user: Annotated[object, Depends(get_current_user)],
    svc: Annotated[UserService, Depends(get_user_service)],
):
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return user
    return await svc.update_profile(user.id, **updates)
