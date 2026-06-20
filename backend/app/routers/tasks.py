from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_task_service, get_current_user
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.repositories.activity_repo import ActivityRepository
from app.schemas.task import AssigneesIn, TaskIn, TaskOut, TaskPatch
from app.services.task_service import TaskService

router = APIRouter(prefix="/api/v1", tags=["tasks"])

Service = Annotated[TaskService, Depends(get_task_service)]
Session = Annotated[AsyncSession, Depends(get_session)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


@router.post("/projects/{project_id}/tasks", response_model=TaskOut,
             status_code=status.HTTP_201_CREATED)
async def create_task(project_id: int, body: TaskIn, ctx: Writer, svc: Service):
    return await svc.create(workspace_id=ctx.workspace_id, project_id=project_id,
                            title=body.title, description=body.description,
                            priority=body.priority, due_date=body.due_date,
                            parent_task_id=body.parent_task_id,
                            assignee_ids=body.assignee_ids)


@router.get("/tasks/{task_id}/subtasks", response_model=list[TaskOut])
async def list_subtasks(task_id: int, ctx: Reader, svc: Service):
    return await svc.list_subtasks(task_id, ctx.workspace_id)


@router.put("/tasks/{task_id}/assignees", response_model=TaskOut)
async def set_task_assignees(task_id: int, body: AssigneesIn, ctx: Writer, svc: Service):
    return await svc.set_assignees(task_id, ctx.workspace_id, body.user_ids)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
async def list_tasks(project_id: int, ctx: Reader, svc: Service,
                     limit: int = Query(200, ge=1, le=500),
                     offset: int = Query(0, ge=0)):
    return await svc.list(workspace_id=ctx.workspace_id, project_id=project_id,
                          limit=limit, offset=offset)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
async def patch_task(task_id: int, body: TaskPatch, ctx: Writer, svc: Service):
    return await svc.update(task_id, ctx.workspace_id, **body.model_dump(exclude_unset=True))


@router.get("/tasks/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, svc: Service, user=Depends(get_current_user)):
    return await svc.get_task_for_user(task_id, user.id)


@router.get("/tasks/{task_id}/activity")
async def task_activity(
    task_id: int,
    ctx: Reader,
    session: Session,
    before: int | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
):
    rows = await ActivityRepository(session).list_for_entity(
        ctx.workspace_id, "task", task_id, before_id=before, limit=limit
    )
    next_cursor = rows[-1]["id"] if len(rows) == limit else None
    return {"items": rows, "next_cursor": next_cursor}


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, ctx: Deleter, svc: Service):
    await svc.delete(task_id, ctx.workspace_id)
