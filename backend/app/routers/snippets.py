from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_snippet_service
from app.schemas.snippet import SnippetIn, SnippetOut, SnippetPatch
from app.services.snippet_service import SnippetService

router = APIRouter(prefix="/api/v1/snippets", tags=["snippets"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[SnippetService, Depends(get_snippet_service)]


@router.post("", response_model=SnippetOut, status_code=status.HTTP_201_CREATED)
async def create_snippet(body: SnippetIn, user: CurrentUser, svc: Service):
    return await svc.create(owner_id=user.id, title=body.title, language=body.language,
                            code=body.code, tags=body.tags, notes=body.notes,
                            project_id=body.project_id)


@router.get("", response_model=list[SnippetOut])
async def list_snippets(user: CurrentUser, svc: Service,
                        project_id: int | None = None,
                        tag: str | None = None,
                        language: str | None = None,
                        limit: int = Query(50, ge=1, le=100),
                        offset: int = Query(0, ge=0)):
    return await svc.list(owner_id=user.id, project_id=project_id, tag=tag,
                          language=language, limit=limit, offset=offset)


@router.get("/{snippet_id}", response_model=SnippetOut)
async def get_snippet(snippet_id: str, user: CurrentUser, svc: Service):
    return await svc.get(snippet_id, user.id)


@router.patch("/{snippet_id}", response_model=SnippetOut)
async def patch_snippet(snippet_id: str, body: SnippetPatch,
                        user: CurrentUser, svc: Service):
    return await svc.update(snippet_id, user.id,
                            fields=body.model_dump(exclude_unset=True))


@router.delete("/{snippet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_snippet(snippet_id: str, user: CurrentUser, svc: Service):
    await svc.delete(snippet_id, user.id)
