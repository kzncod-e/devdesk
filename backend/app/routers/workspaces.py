from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_workspace_service
from app.api.tenancy import require_member
from app.core.policy import Perm
from app.models.workspace import Membership
from app.schemas.workspace import (
    AcceptInviteIn,
    InviteCreatedOut,
    InviteIn,
    InviteOut,
    MemberOut,
    RolePatch,
    WorkspaceIn,
    WorkspaceWithRoleOut,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/api/v1", tags=["workspaces"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Service = Annotated[WorkspaceService, Depends(get_workspace_service)]
Manager = Annotated[Membership, Depends(require_member(Perm.MEMBER_MANAGE))]
AnyMember = Annotated[Membership, Depends(require_member())]


@router.post("/workspaces", response_model=WorkspaceWithRoleOut,
             status_code=status.HTTP_201_CREATED)
async def create_workspace(body: WorkspaceIn, user: CurrentUser, svc: Service):
    ws = await svc.create(user_id=user.id, name=body.name)
    return WorkspaceWithRoleOut(id=ws.id, name=ws.name, slug=ws.slug, plan=ws.plan, role="owner")


@router.get("/workspaces", response_model=list[WorkspaceWithRoleOut])
async def list_workspaces(user: CurrentUser, svc: Service):
    rows = await svc.list_mine(user.id)
    return [
        WorkspaceWithRoleOut(id=w.id, name=w.name, slug=w.slug, plan=w.plan, role=role)
        for w, role in rows
    ]


@router.get("/workspaces/{workspace_id}/members", response_model=list[MemberOut])
async def list_members(workspace_id: int, svc: Service, _: AnyMember):
    return await svc.members(workspace_id)


@router.post("/workspaces/{workspace_id}/invites", response_model=InviteCreatedOut,
             status_code=status.HTTP_201_CREATED)
async def invite_member(workspace_id: int, body: InviteIn, svc: Service, actor: Manager):
    invite, token = await svc.invite(
        actor=actor, workspace_id=workspace_id, email=body.email, role=body.role
    )
    return InviteCreatedOut(
        id=invite.id, email=invite.email, role=invite.role,
        expires_at=invite.expires_at, accepted_at=invite.accepted_at, token=token,
    )


@router.get("/workspaces/{workspace_id}/invites", response_model=list[InviteOut])
async def list_invites(workspace_id: int, svc: Service, _: Manager):
    return await svc.list_invites(workspace_id)


@router.patch("/workspaces/{workspace_id}/members/{user_id}", response_model=MemberOut)
async def change_member_role(workspace_id: int, user_id: int, body: RolePatch,
                             svc: Service, actor: Manager):
    await svc.change_role(actor=actor, workspace_id=workspace_id,
                          target_user_id=user_id, new_role=body.role)
    members = await svc.members(workspace_id)
    return next(m for m in members if m["user_id"] == user_id)


@router.delete("/workspaces/{workspace_id}/members/{user_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(workspace_id: int, user_id: int, svc: Service, actor: Manager):
    await svc.remove_member(actor=actor, workspace_id=workspace_id, target_user_id=user_id)


@router.post("/invites/accept")
async def accept_invite(body: AcceptInviteIn, user: CurrentUser, svc: Service):
    membership = await svc.accept_invite(user=user, token=body.token)
    return {"workspace_id": membership.workspace_id, "role": membership.role}
