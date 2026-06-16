from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_search_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.schemas.search import SearchOut
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])

Service = Annotated[SearchService, Depends(get_search_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]


@router.get("", response_model=SearchOut)
async def search(ctx: Reader, svc: Service,
                 q: str = Query(min_length=1, max_length=200),
                 limit: int = Query(10, ge=1, le=50),
                 types: str | None = Query(
                     default=None,
                     description="Comma-separated subset of "
                                 "projects,tasks,snippets,bookmarks")):
    type_set = {t.strip() for t in types.split(",") if t.strip()} if types else None
    return await svc.search(workspace_id=ctx.workspace_id, q=q,
                            limit_per_group=limit, types=type_set)
