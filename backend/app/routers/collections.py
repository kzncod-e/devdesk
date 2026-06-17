from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_collection_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.schemas.organization import CollectionIn, CollectionOut, CollectionPatch
from app.services.collection_service import CollectionService

router = APIRouter(prefix="/api/v1/collections", tags=["collections"])

Service = Annotated[CollectionService, Depends(get_collection_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


@router.post("", response_model=CollectionOut, status_code=status.HTTP_201_CREATED)
async def create_collection(body: CollectionIn, ctx: Writer, svc: Service):
    return await svc.create(workspace_id=ctx.workspace_id, name=body.name,
                            kind=body.kind, parent_id=body.parent_id)


@router.get("", response_model=list[CollectionOut])
async def list_collections(ctx: Reader, svc: Service,
                           kind: str | None = Query(default=None)):
    return await svc.list(ctx.workspace_id, kind=kind)


@router.patch("/{collection_id}", response_model=CollectionOut)
async def patch_collection(collection_id: int, body: CollectionPatch, ctx: Writer,
                           svc: Service):
    return await svc.update(
        collection_id, ctx.workspace_id,
        name=body.name, parent_id=body.parent_id,
        set_parent="parent_id" in body.model_fields_set,
    )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(collection_id: int, ctx: Deleter, svc: Service):
    await svc.delete(collection_id, ctx.workspace_id)
