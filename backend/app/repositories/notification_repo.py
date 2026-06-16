from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


def _to_api(row: Notification) -> dict:
    return {
        "id": row.id,
        "workspace_id": row.workspace_id,
        "type": row.type,
        "payload": row.payload or {},
        "read_at": row.read_at.isoformat() if row.read_at else None,
        "created_at": row.created_at.isoformat(),
    }


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        workspace_id: int,
        type: str,
        payload: dict,
    ) -> Notification:
        row = Notification(
            user_id=user_id,
            workspace_id=workspace_id,
            type=type,
            payload=payload,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_for_user(
        self,
        user_id: int,
        *,
        before_id: int | None = None,
        limit: int = 30,
    ) -> list[dict]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if before_id is not None:
            stmt = stmt.where(Notification.id < before_id)
        stmt = stmt.order_by(Notification.id.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return [_to_api(row) for row in res.scalars().all()]

    async def unread_count(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        res = await self.session.execute(stmt)
        return int(res.scalar_one())

    async def mark_read(
        self,
        user_id: int,
        *,
        ids: list[int] | None = None,
        mark_all: bool = False,
    ) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=now)
        )
        if not mark_all:
            if not ids:
                return 0
            stmt = stmt.where(Notification.id.in_(ids))
        res = await self.session.execute(stmt)
        return int(res.rowcount)

    async def list_unread_for_digest(self, *, since: datetime) -> list[Notification]:
        """Unread notifications created since `since`, grouped by user in the caller."""
        stmt = (
            select(Notification)
            .where(
                Notification.read_at.is_(None),
                Notification.created_at >= since,
            )
            .order_by(Notification.user_id, Notification.created_at)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get(self, notification_id: int) -> Notification | None:
        return await self.session.get(Notification, notification_id)
