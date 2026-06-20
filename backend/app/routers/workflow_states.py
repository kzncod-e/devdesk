from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_workflow_state_service
from app.api.tenancy import WorkspaceContext, require
from app.core.policy import Perm
from app.schemas.workflow_state import WorkflowStateIn, WorkflowStateOut, WorkflowStatePatch
from app.services.workflow_state_service import WorkflowStateService

router = APIRouter(prefix="/api/v1", tags=["workflow_states"])

Service = Annotated[WorkflowStateService, Depends(get_workflow_state_service)]
Reader = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_READ))]
Writer = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_WRITE))]
Deleter = Annotated[WorkspaceContext, Depends(require(Perm.CONTENT_DELETE))]


@router.get("/projects/{project_id}/states", response_model=list[WorkflowStateOut])
async def list_states(project_id: int, ctx: Reader, svc: Service):
    return await svc.list(project_id, ctx.workspace_id)


@router.post("/projects/{project_id}/states", response_model=WorkflowStateOut,
             status_code=status.HTTP_201_CREATED)
async def create_state(project_id: int, body: WorkflowStateIn, ctx: Writer, svc: Service):
    return await svc.create(project_id, ctx.workspace_id, name=body.name,
                            category=body.category, color=body.color)


@router.patch("/projects/{project_id}/states/{state_id}", response_model=WorkflowStateOut)
async def update_state(project_id: int, state_id: int, body: WorkflowStatePatch,
                       ctx: Writer, svc: Service):
    return await svc.update(state_id, project_id, ctx.workspace_id,
                            **body.model_dump(exclude_unset=True))


@router.delete("/projects/{project_id}/states/{state_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(project_id: int, state_id: int, ctx: Deleter, svc: Service):
    await svc.delete(state_id, project_id, ctx.workspace_id)
