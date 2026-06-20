from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_comment_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm, can
from app.schemas.comment import CommentIn, CommentOut, CommentPatch
from app.services.comment_service import CommentService

router = APIRouter(prefix="/api/v1", tags=["comments"])

Service = Annotated[CommentService, Depends(get_comment_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Commenter = Annotated[WorkspaceContext, Depends(require(Perm.COMMENT_WRITE))]


@router.get("/comments", response_model=list[CommentOut])
async def list_comments(
    ctx: Reader,
    svc: Service,
    entity_type: str = Query(pattern=r"^(task)$"),
    entity_id: int = Query(ge=1),
):
    return await svc.list(
        entity_type=entity_type, entity_id=entity_id, workspace_id=ctx.workspace_id
    )


@router.post("/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(body: CommentIn, ctx: Commenter, svc: Service):
    return await svc.create(
        workspace_id=ctx.workspace_id,
        author_id=ctx.user.id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        body=body.body,
        parent_id=body.parent_id,
        mention_ids=body.mention_ids,
    )


@router.patch("/comments/{comment_id}", response_model=CommentOut)
async def update_comment(comment_id: int, body: CommentPatch, ctx: Reader, svc: Service):
    return await svc.update(
        comment_id, workspace_id=ctx.workspace_id, user_id=ctx.user.id, body=body.body
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: int, ctx: Reader, svc: Service):
    await svc.delete(
        comment_id,
        workspace_id=ctx.workspace_id,
        user_id=ctx.user.id,
        can_moderate=can(ctx.role, Perm.CONTENT_DELETE),
    )
