from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Invite, Membership, Workspace


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, name: str, slug: str, created_by: int) -> Workspace:
        ws = Workspace(name=name, slug=slug, created_by=created_by)
        self.session.add(ws)
        await self.session.flush()  # assign id without ending the transaction
        return ws

    async def get(self, workspace_id: int) -> Workspace | None:
        return await self.session.get(Workspace, workspace_id)

    async def slug_exists(self, slug: str) -> bool:
        res = await self.session.execute(select(Workspace.id).where(Workspace.slug == slug))
        return res.first() is not None

    async def list_for_user(self, user_id: int) -> list[tuple[Workspace, str]]:
        """Workspaces the user belongs to, paired with their role in each."""
        stmt = (
            select(Workspace, Membership.role)
            .join(Membership, Membership.workspace_id == Workspace.id)
            .where(Membership.user_id == user_id, Membership.status == "active")
            .order_by(Workspace.created_at)
        )
        res = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in res.all()]


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, *, workspace_id: int, user_id: int, role: str,
                  invited_by: int | None = None, status: str = "active") -> Membership:
        m = Membership(workspace_id=workspace_id, user_id=user_id, role=role,
                       invited_by=invited_by, status=status)
        self.session.add(m)
        await self.session.flush()
        return m

    async def get(self, workspace_id: int, user_id: int) -> Membership | None:
        stmt = select(Membership).where(
            Membership.workspace_id == workspace_id, Membership.user_id == user_id
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_default_for_user(self, user_id: int) -> Membership | None:
        """The user's fallback workspace when no X-Workspace-Id is supplied —
        their oldest active membership (typically the personal workspace)."""
        stmt = (
            select(Membership)
            .where(Membership.user_id == user_id, Membership.status == "active")
            .order_by(Membership.id)
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_with_users(self, workspace_id: int) -> list[tuple[Membership, User]]:
        stmt = (
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.workspace_id == workspace_id)
            .order_by(User.name)
        )
        res = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in res.all()]

    async def count_owners(self, workspace_id: int) -> int:
        stmt = select(func.count()).select_from(Membership).where(
            Membership.workspace_id == workspace_id,
            Membership.role == "owner",
            Membership.status == "active",
        )
        res = await self.session.execute(stmt)
        return int(res.scalar_one())

    async def update(self, membership: Membership, **fields) -> Membership:
        for key, value in fields.items():
            setattr(membership, key, value)
        await self.session.flush()
        return membership

    async def delete(self, membership: Membership) -> None:
        await self.session.delete(membership)
        await self.session.flush()


class InviteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, *, workspace_id: int, email: str, role: str,
                     token_hash: str, invited_by: int, expires_at: datetime) -> Invite:
        existing = await self._get_pending(workspace_id, email)
        if existing is not None:
            existing.role = role
            existing.token_hash = token_hash
            existing.invited_by = invited_by
            existing.expires_at = expires_at
            existing.accepted_at = None
            await self.session.flush()
            return existing
        invite = Invite(workspace_id=workspace_id, email=email, role=role,
                        token_hash=token_hash, invited_by=invited_by, expires_at=expires_at)
        self.session.add(invite)
        await self.session.flush()
        return invite

    async def _get_pending(self, workspace_id: int, email: str) -> Invite | None:
        stmt = select(Invite).where(
            Invite.workspace_id == workspace_id, Invite.email == email
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_hash(self, token_hash: str) -> Invite | None:
        stmt = select(Invite).where(Invite.token_hash == token_hash)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_pending(self, workspace_id: int) -> list[Invite]:
        stmt = (
            select(Invite)
            .where(Invite.workspace_id == workspace_id, Invite.accepted_at.is_(None))
            .order_by(Invite.created_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
