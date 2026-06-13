from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_admin_user, get_user_service
from app.schemas.auth import UserOut, UserRolePatch
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

AdminUser = Annotated[object, Depends(get_admin_user)]
UserSvc = Annotated[UserService, Depends(get_user_service)]


@router.get("/users", response_model=list[UserOut])
async def list_users(
    _admin: AdminUser,
    svc: UserSvc,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await svc.list_users(limit=limit, offset=offset)


@router.patch("/users/{user_id}/role", response_model=UserOut)
async def set_user_role(
    user_id: int,
    body: UserRolePatch,
    _admin: AdminUser,
    svc: UserSvc,
):
    return await svc.set_role(user_id, body.role)
