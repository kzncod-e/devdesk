from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.api.deps import get_bookmark_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.schemas.bookmark import BookmarkIn, BookmarkOut, BookmarkPatch
from app.services.bookmark_service import BookmarkService

router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])

Service = Annotated[BookmarkService, Depends(get_bookmark_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


@router.post("", response_model=BookmarkOut, status_code=status.HTTP_201_CREATED)
async def create_bookmark(body: BookmarkIn, ctx: Writer, svc: Service,
                          background_tasks: BackgroundTasks):
    doc = await svc.create(workspace_id=ctx.workspace_id, owner_id=ctx.user.id,
                           url=str(body.url), tags=body.tags, project_id=body.project_id)
    background_tasks.add_task(svc.fetch_and_store_meta, doc["id"], doc["url"])
    return doc


@router.get("", response_model=list[BookmarkOut])
async def list_bookmarks(ctx: Reader, svc: Service,
                         project_id: int | None = None,
                         tag: str | None = None,
                         limit: int = Query(50, ge=1, le=100),
                         offset: int = Query(0, ge=0)):
    return await svc.list(workspace_id=ctx.workspace_id, project_id=project_id, tag=tag,
                          limit=limit, offset=offset)


@router.get("/{bookmark_id}", response_model=BookmarkOut)
async def get_bookmark(bookmark_id: int, ctx: Reader, svc: Service):
    return await svc.get(bookmark_id, ctx.workspace_id)


@router.patch("/{bookmark_id}", response_model=BookmarkOut)
async def patch_bookmark(bookmark_id: int, body: BookmarkPatch, ctx: Writer, svc: Service):
    return await svc.update(bookmark_id, ctx.workspace_id,
                            fields=body.model_dump(exclude_unset=True))


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(bookmark_id: int, ctx: Deleter, svc: Service):
    await svc.delete(bookmark_id, ctx.workspace_id)
