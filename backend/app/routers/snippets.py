from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_snippet_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.schemas.snippet import SnippetIn, SnippetOut, SnippetPatch
from app.services.snippet_service import SnippetService

router = APIRouter(prefix="/api/v1/snippets", tags=["snippets"])

Service = Annotated[SnippetService, Depends(get_snippet_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


@router.post("", response_model=SnippetOut, status_code=status.HTTP_201_CREATED)
async def create_snippet(body: SnippetIn, ctx: Writer, svc: Service):
    return await svc.create(workspace_id=ctx.workspace_id, owner_id=ctx.user.id,
                            title=body.title, language=body.language, code=body.code,
                            tags=body.tags, notes=body.notes, project_id=body.project_id)


@router.get("", response_model=list[SnippetOut])
async def list_snippets(ctx: Reader, svc: Service,
                        project_id: int | None = None,
                        tag: str | None = None,
                        language: str | None = None,
                        limit: int = Query(50, ge=1, le=100),
                        offset: int = Query(0, ge=0)):
    return await svc.list(workspace_id=ctx.workspace_id, project_id=project_id, tag=tag,
                          language=language, limit=limit, offset=offset)


@router.get("/{snippet_id}", response_model=SnippetOut)
async def get_snippet(snippet_id: int, ctx: Reader, svc: Service):
    return await svc.get(snippet_id, ctx.workspace_id)


@router.patch("/{snippet_id}", response_model=SnippetOut)
async def patch_snippet(snippet_id: int, body: SnippetPatch, ctx: Writer, svc: Service):
    return await svc.update(snippet_id, ctx.workspace_id,
                            fields=body.model_dump(exclude_unset=True))


@router.delete("/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snippet(snippet_id: int, ctx: Deleter, svc: Service):
    await svc.delete(snippet_id, ctx.workspace_id)
