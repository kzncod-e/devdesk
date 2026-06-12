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
