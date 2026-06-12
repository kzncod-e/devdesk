from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_search_service
from app.schemas.search import SearchOut
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[SearchService, Depends(get_search_service)]


@router.get("", response_model=SearchOut)
async def search(user: CurrentUser, svc: Service,
                 q: str = Query(min_length=1, max_length=200),
                 limit: int = Query(10, ge=1, le=50)):
    return await svc.search(owner_id=user.id, q=q, limit_per_group=limit)
