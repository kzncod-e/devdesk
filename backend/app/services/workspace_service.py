import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, UnprocessableError
from app.core.policy import Role, is_valid_role, rank
from app.models.workspace import Membership
from app.repositories.user_repo import UserRepository
from app.repositories.workspace_repo import (
    InviteRepository,
    MembershipRepository,
    WorkspaceRepository,
)

INVITE_TTL_DAYS = 7


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return base or "workspace"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class WorkspaceService:
    """Owns the workspace/membership/invite unit of work. Repos `flush`; the
    service `commit`s, so multi-entity operations stay atomic."""

    def __init__(self, session, workspaces: WorkspaceRepository,
                 memberships: MembershipRepository, invites: InviteRepository,
                 users: UserRepository) -> None:
        self.session = session
        self.workspaces = workspaces
        self.memberships = memberships
        self.invites = invites
        self.users = users

    # ── Workspaces ────────────────────────────────────────────────────────
    async def create(self, *, user_id: int, name: str):
        slug = _slugify(name)
        if await self.workspaces.slug_exists(slug):
            slug = f"{slug}-{secrets.token_hex(3)}"
        ws = await self.workspaces.create(name=name, slug=slug, created_by=user_id)
        await self.memberships.add(workspace_id=ws.id, user_id=user_id, role=Role.OWNER)
        await self.session.commit()
        await self.session.refresh(ws)
        return ws

    async def list_mine(self, user_id: int) -> list[tuple]:
        return await self.workspaces.list_for_user(user_id)

    # ── Members ───────────────────────────────────────────────────────────
    async def members(self, workspace_id: int) -> list[dict]:
        rows = await self.memberships.list_with_users(workspace_id)
        return [
            {
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "avatar_url": u.avatar_url,
                "role": m.role,
                "status": m.status,
            }
            for m, u in rows
        ]

    async def change_role(self, *, actor: Membership, workspace_id: int,
                          target_user_id: int, new_role: str) -> Membership:
        if not is_valid_role(new_role):
            raise UnprocessableError(f"Invalid role: {new_role}")
        target = await self._require_membership(workspace_id, target_user_id)
        self._guard_can_manage(actor, target)
        if rank(new_role) > rank(actor.role):
            raise ForbiddenError("Cannot assign a role above your own")
        # Don't strip the last owner of ownership.
        if target.role == Role.OWNER and new_role != Role.OWNER:
            await self._guard_not_last_owner(workspace_id)
        updated = await self.memberships.update(target, role=new_role)
        await self.session.commit()
        return updated

    async def remove_member(self, *, actor: Membership, workspace_id: int,
                            target_user_id: int) -> None:
        target = await self._require_membership(workspace_id, target_user_id)
        if target.id != actor.id:  # allow self-leave; otherwise rank-gate
            self._guard_can_manage(actor, target)
        if target.role == Role.OWNER:
            await self._guard_not_last_owner(workspace_id)
        await self.memberships.delete(target)
        await self.session.commit()

    # ── Invites ───────────────────────────────────────────────────────────
    async def invite(self, *, actor: Membership, workspace_id: int,
                     email: str, role: str) -> tuple:
        if rank(role) > rank(actor.role):
            raise ForbiddenError("Cannot invite at a role above your own")
        existing_user = await self.users.get_by_email(email)
        if existing_user is not None:
            if await self.memberships.get(workspace_id, existing_user.id) is not None:
                raise ConflictError("That user is already a member")
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS)
        invite = await self.invites.upsert(
            workspace_id=workspace_id, email=email, role=role,
            token_hash=_hash_token(token), invited_by=actor.user_id, expires_at=expires,
        )
        await self.session.commit()
        await self.session.refresh(invite)
        return invite, token

    async def list_invites(self, workspace_id: int):
        return await self.invites.list_pending(workspace_id)

    async def accept_invite(self, *, user, token: str) -> Membership:
        invite = await self.invites.get_by_hash(_hash_token(token))
        if invite is None or invite.accepted_at is not None:
            raise NotFoundError("Invite not found or already used")
        # SQLite (test tier) returns naive datetimes; treat them as UTC.
        expires_at = invite.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise UnprocessableError("Invite has expired")
        if invite.email.lower() != user.email.lower():
            raise ForbiddenError("This invite was issued to a different email")

        membership = await self.memberships.get(invite.workspace_id, user.id)
        if membership is None:
            membership = await self.memberships.add(
                workspace_id=invite.workspace_id, user_id=user.id,
                role=invite.role, invited_by=invite.invited_by,
            )
        else:
            await self.memberships.update(membership, status="active", role=invite.role)
        invite.accepted_at = datetime.now(timezone.utc)
        await self.session.commit()
        return membership

    # ── Invariants ────────────────────────────────────────────────────────
    async def _require_membership(self, workspace_id: int, user_id: int) -> Membership:
        m = await self.memberships.get(workspace_id, user_id)
        if m is None:
            raise NotFoundError("Member not found")
        return m

    def _guard_can_manage(self, actor: Membership, target: Membership) -> None:
        # You cannot manage a peer or anyone ranked above you.
        if rank(target.role) >= rank(actor.role):
            raise ForbiddenError("Cannot manage a member at or above your role")

    async def _guard_not_last_owner(self, workspace_id: int) -> None:
        if await self.memberships.count_owners(workspace_id) <= 1:
            raise UnprocessableError("A workspace must keep at least one owner")
