"""Workspace scoping + RBAC enforcement for the request layer.

Two entry points:
- `get_workspace_context` / `require(perm)` — header-based (`X-Workspace-Id`),
  for content routers that operate "inside the current workspace".
- `require_member(perm)` — path-based (`/workspaces/{workspace_id}/...`), for
  workspace-management routes.
"""
from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.errors import ForbiddenError
from app.core.policy import Perm, can
from app.db.postgres import get_session
from app.models.workspace import Membership
from app.repositories.workspace_repo import MembershipRepository


@dataclass
class WorkspaceContext:
    user: object
    workspace_id: int
    role: str
    membership: Membership


async def get_workspace_context(
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    workspace_id: int | None = Header(default=None, alias="X-Workspace-Id"),
) -> WorkspaceContext:
    repo = MembershipRepository(session)
    if workspace_id is None:
        # No explicit workspace selected — fall back to the user's default.
        membership = await repo.get_default_for_user(user.id)
        if membership is None:
            raise ForbiddenError("No workspace available")
    else:
        membership = await repo.get(workspace_id, user.id)
        if membership is None or membership.status != "active":
            raise ForbiddenError("Not a member of this workspace")
    return WorkspaceContext(
        user=user, workspace_id=membership.workspace_id, role=membership.role,
        membership=membership,
    )


def require(perm: Perm):
    """Header-scoped permission guard. Use in content routers (increment 2)."""

    async def guard(ctx: WorkspaceContext = Depends(get_workspace_context)) -> WorkspaceContext:
        if not can(ctx.role, perm):
            raise ForbiddenError(f"Missing permission: {perm.value}")
        return ctx

    return guard


def require_member(perm: Perm | None = None):
    """Path-scoped guard: resolves `{workspace_id}` from the route, loads the
    caller's membership, and (optionally) checks a permission. Returns the
    caller's Membership so handlers can enforce further invariants."""

    async def guard(
        workspace_id: int,
        user=Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
    ) -> Membership:
        membership = await MembershipRepository(session).get(workspace_id, user.id)
        if membership is None or membership.status != "active":
            raise ForbiddenError("Not a member of this workspace")
        if perm is not None and not can(membership.role, perm):
            raise ForbiddenError(f"Missing permission: {perm.value}")
        return membership

    return guard
