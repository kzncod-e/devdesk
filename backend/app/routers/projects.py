import time
from typing import Annotated

import cloudinary
import cloudinary.utils
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_project_service, get_current_user
from app.api.tenancy import WorkspaceContext, require
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.policy import Perm
from app.schemas.project import ProjectIn, ProjectOut, ProjectPatch
from app.schemas.task import ProjectSummaryOut
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

Service = Annotated[ProjectService, Depends(get_project_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectIn, ctx: Writer, svc: Service):
    return await svc.create(workspace_id=ctx.workspace_id, owner_id=ctx.user.id,
                            name=body.name, description=body.description, color=body.color)


@router.get("", response_model=list[ProjectOut])
async def list_projects(ctx: Reader, svc: Service,
                        limit: int = Query(50, ge=1, le=100),
                        offset: int = Query(0, ge=0)):
    return await svc.list(ctx.workspace_id, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, svc: Service, user=Depends(get_current_user)):
    return await svc.get_project_for_user(project_id, user.id)


@router.get("/{project_id}/summary", response_model=ProjectSummaryOut)
async def project_summary(project_id: int, svc: Service, user=Depends(get_current_user)):
    return await svc.get_project_summary_for_user(project_id, user.id)


@router.patch("/{project_id}", response_model=ProjectOut)
async def patch_project(project_id: int, body: ProjectPatch, ctx: Writer, svc: Service):
    return await svc.update(project_id, ctx.workspace_id,
                            **body.model_dump(exclude_unset=True))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, ctx: Deleter, svc: Service):
    await svc.delete(project_id, ctx.workspace_id)


@router.get("/{project_id}/upload-signature")
async def get_upload_signature(project_id: int, ctx: Writer, svc: Service):
    """Returns a signed upload token so the browser can POST directly to Cloudinary."""
    await svc.get(project_id, ctx.workspace_id)  # verifies project is in this workspace

    settings = get_settings()
    if not settings.cloudinary_cloud_name:
        raise AppError("Image upload is not configured (missing Cloudinary credentials)")

    public_id = f"devdesk/projects/project_{project_id}"
    timestamp = int(time.time())
    params_to_sign = {"public_id": public_id, "timestamp": timestamp}
    signature = cloudinary.utils.api_sign_request(params_to_sign, settings.cloudinary_api_secret)

    return {
        "signature": signature,
        "timestamp": timestamp,
        "api_key": settings.cloudinary_api_key,
        "cloud_name": settings.cloudinary_cloud_name,
        "public_id": public_id,
    }
