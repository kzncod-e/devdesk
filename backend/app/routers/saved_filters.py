from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_saved_filter_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.schemas.organization import SavedFilterIn, SavedFilterOut
from app.services.saved_filter_service import SavedFilterService

router = APIRouter(prefix="/api/v1/saved-filters", tags=["saved-filters"])

Service = Annotated[SavedFilterService, Depends(get_saved_filter_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]


@router.post("", response_model=SavedFilterOut, status_code=status.HTTP_201_CREATED)
async def create_saved_filter(body: SavedFilterIn, ctx: Reader, svc: Service):
    return await svc.create(user_id=ctx.user.id, workspace_id=ctx.workspace_id,
                            name=body.name, kind=body.kind, query=body.query)


@router.get("", response_model=list[SavedFilterOut])
async def list_saved_filters(ctx: Reader, svc: Service,
                             kind: str | None = Query(default=None)):
    return await svc.list(user_id=ctx.user.id, workspace_id=ctx.workspace_id, kind=kind)


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_filter(filter_id: int, ctx: Reader, svc: Service):
    await svc.delete(filter_id, user_id=ctx.user.id)
