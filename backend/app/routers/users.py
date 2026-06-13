from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_user_service
from app.schemas.task import UserBrief
from app.services.user_service import UserService

router = APIRouter(prefix="/api/v1", tags=["users"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[UserService, Depends(get_user_service)]


@router.get("/users", response_model=list[UserBrief])
async def list_users(user: CurrentUser, svc: Service,
                     limit: int = Query(100, ge=1, le=200),
                     offset: int = Query(0, ge=0)):
    """Brief list of all users — used for the task assignee picker."""
    return await svc.list_users(limit=limit, offset=offset)
