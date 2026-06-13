import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.deps import get_current_user, get_project_service
from app.core.errors import UnprocessableError
from app.schemas.project import ProjectIn, ProjectOut, ProjectPatch
from app.schemas.task import ProjectSummaryOut
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[ProjectService, Depends(get_project_service)]

_UPLOAD_ROOT = Path("/app/static/uploads/projects")
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MIME_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


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


@router.post("/{project_id}/image", response_model=ProjectOut)
async def upload_project_image(
    project_id: int,
    user: CurrentUser,
    svc: Service,
    file: UploadFile = File(...),
):
    await svc.get(project_id, user.id)  # verifies ownership, raises NotFoundError if not owner

    if file.content_type not in _ALLOWED_MIME:
        raise UnprocessableError(
            f"Unsupported file type '{file.content_type}'. Allowed: JPEG, PNG, WebP, GIF"
        )

    data = await file.read()
    if len(data) > _MAX_IMAGE_BYTES:
        raise UnprocessableError("Image must be smaller than 5 MB")

    ext = _MIME_EXT[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    _UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    ((_UPLOAD_ROOT / filename)).write_bytes(data)

    image_url = f"/static/uploads/projects/{filename}"
    return await svc.update(project_id, user.id, image_url=image_url)
