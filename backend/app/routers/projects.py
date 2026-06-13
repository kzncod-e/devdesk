import time
from typing import Annotated

import cloudinary
import cloudinary.utils
from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_project_service
from app.core.config import get_settings
from app.core.errors import AppError
from app.schemas.project import ProjectIn, ProjectOut, ProjectPatch
from app.schemas.task import ProjectSummaryOut
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[ProjectService, Depends(get_project_service)]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectIn, user: CurrentUser, svc: Service):
    return await svc.create(owner_id=user.id, name=body.name,
                            description=body.description, color=body.color)


@router.get("", response_model=list[ProjectOut])
async def list_projects(user: CurrentUser, svc: Service,
                        limit: int = Query(50, ge=1, le=100),
                        offset: int = Query(0, ge=0)):
    return await svc.list(user.id, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, user: CurrentUser, svc: Service):
    return await svc.get(project_id, user.id)


@router.get("/{project_id}/summary", response_model=ProjectSummaryOut)
async def project_summary(project_id: int, user: CurrentUser, svc: Service):
    return await svc.summary(project_id, user.id)


@router.patch("/{project_id}", response_model=ProjectOut)
async def patch_project(project_id: int, body: ProjectPatch,
                        user: CurrentUser, svc: Service):
    return await svc.update(project_id, user.id,
                            **body.model_dump(exclude_unset=True))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, user: CurrentUser, svc: Service):
    await svc.delete(project_id, user.id)


@router.get("/{project_id}/upload-signature")
async def get_upload_signature(project_id: int, user: CurrentUser, svc: Service):
    """Returns a signed upload token so the browser can POST directly to Cloudinary."""
    await svc.get(project_id, user.id)  # verifies ownership

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
