from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_tag_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.schemas.organization import TagColorPatch, TagOut
from app.services.tag_service import TagService

router = APIRouter(prefix="/api/v1/tags", tags=["tags"])

Service = Annotated[TagService, Depends(get_tag_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


@router.get("", response_model=list[TagOut])
async def list_tags(ctx: Reader, svc: Service):
    return await svc.list(ctx.workspace_id)


@router.patch("/{tag_id}", response_model=TagOut)
async def recolor_tag(tag_id: int, body: TagColorPatch, ctx: Writer, svc: Service):
    return await svc.set_color(tag_id, ctx.workspace_id, color=body.color)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, ctx: Deleter, svc: Service):
    await svc.delete(tag_id, ctx.workspace_id)
