from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_task_service
from app.schemas.task import TaskIn, TaskOut, TaskPatch
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/v1", tags=["tasks"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[TaskService, Depends(get_task_service)]


@router.post("/projects/{project_id}/tasks", response_model=TaskOut,
             status_code=status.HTTP_201_CREATED)
async def create_task(project_id: int, body: TaskIn, user: CurrentUser, svc: Service):
    return await svc.create(owner_id=user.id, project_id=project_id, title=body.title,
                            description=body.description, priority=body.priority,
                            due_date=body.due_date)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
async def list_tasks(project_id: int, user: CurrentUser, svc: Service,
                     limit: int = Query(200, ge=1, le=500),
                     offset: int = Query(0, ge=0)):
    return await svc.list(owner_id=user.id, project_id=project_id,
                          limit=limit, offset=offset)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def patch_task(task_id: int, body: TaskPatch, user: CurrentUser, svc: Service):
    return await svc.update(task_id, user.id, **body.model_dump(exclude_unset=True))


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, user: CurrentUser, svc: Service):
    await svc.delete(task_id, user.id)
