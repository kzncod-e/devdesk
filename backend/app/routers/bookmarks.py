from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.api.deps import get_bookmark_service, get_current_user
from app.schemas.bookmark import BookmarkIn, BookmarkOut, BookmarkPatch
from app.services.bookmark_service import BookmarkService

router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[BookmarkService, Depends(get_bookmark_service)]


@router.post("", response_model=BookmarkOut, status_code=status.HTTP_201_CREATED)
async def create_bookmark(body: BookmarkIn, user: CurrentUser, svc: Service,
                          background_tasks: BackgroundTasks):
    doc = await svc.create(owner_id=user.id, url=str(body.url), tags=body.tags,
                           project_id=body.project_id)
    background_tasks.add_task(svc.fetch_and_store_meta, doc["id"], doc["url"])
    return doc


@router.get("", response_model=list[BookmarkOut])
async def list_bookmarks(user: CurrentUser, svc: Service,
                         project_id: int | None = None,
                         tag: str | None = None,
                         limit: int = Query(50, ge=1, le=100),
                         offset: int = Query(0, ge=0)):
    return await svc.list(owner_id=user.id, project_id=project_id, tag=tag,
                          limit=limit, offset=offset)


@router.get("/{bookmark_id}", response_model=BookmarkOut)
async def get_bookmark(bookmark_id: str, user: CurrentUser, svc: Service):
    return await svc.get(bookmark_id, user.id)


@router.patch("/{bookmark_id}", response_model=BookmarkOut)
async def patch_bookmark(bookmark_id: str, body: BookmarkPatch,
                         user: CurrentUser, svc: Service):
    return await svc.update(bookmark_id, user.id,
                            fields=body.model_dump(exclude_unset=True))


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(bookmark_id: str, user: CurrentUser, svc: Service):
    await svc.delete(bookmark_id, user.id)
