from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_template_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm, can
from app.schemas.template import (
    CaptureIn,
    TemplateDetailOut,
    TemplateIn,
    TemplateOut,
    UseResultOut,
)
from app.services.template_service import TemplateService

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

Service = Annotated[TemplateService, Depends(get_template_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


# ── Public gallery (no auth) — declared before /{id} so it isn't shadowed ──────
@router.get("/gallery", response_model=list[TemplateOut])
async def gallery(svc: Service,
                  kind: str | None = Query(default=None),
                  limit: int = Query(default=50, ge=1, le=100)):
    return await svc.gallery(kind=kind, limit=limit)


@router.get("", response_model=list[TemplateOut])
async def list_templates(ctx: Reader, svc: Service,
                         kind: str | None = Query(default=None),
                         visibility: str | None = Query(default=None)):
    return await svc.list(workspace_id=ctx.workspace_id, kind=kind, visibility=visibility)


@router.post("/capture", response_model=TemplateDetailOut,
             status_code=status.HTTP_201_CREATED)
async def capture(body: CaptureIn, ctx: Writer, svc: Service):
    return await svc.capture(
        workspace_id=ctx.workspace_id, created_by=ctx.user.id,
        kind=body.kind, source_id=body.source_id, name=body.name,
        description=body.description, visibility=body.visibility,
        can_publish=can(ctx.role, Perm.WORKSPACE_MANAGE),
    )


@router.post("", response_model=TemplateDetailOut, status_code=status.HTTP_201_CREATED)
async def create_template(body: TemplateIn, ctx: Writer, svc: Service):
    return await svc.create_from_payload(
        workspace_id=ctx.workspace_id, created_by=ctx.user.id,
        kind=body.kind, name=body.name, description=body.description,
        payload=body.payload, visibility=body.visibility,
        can_publish=can(ctx.role, Perm.WORKSPACE_MANAGE),
    )


@router.get("/{template_id}", response_model=TemplateDetailOut)
async def get_template(template_id: int, ctx: Reader, svc: Service):
    return await svc.get(template_id, workspace_id=ctx.workspace_id)


@router.post("/{template_id}/use", response_model=UseResultOut)
async def use_template(template_id: int, ctx: Writer, svc: Service):
    return await svc.use(template_id, workspace_id=ctx.workspace_id, owner_id=ctx.user.id)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, ctx: Deleter, svc: Service):
    await svc.delete(template_id, workspace_id=ctx.workspace_id)
