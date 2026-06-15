from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User


def _to_api(row) -> dict:
    a: AuditLog = row.AuditLog
    return {
        "id": a.id,
        "workspace_id": a.workspace_id,
        "actor_id": a.actor_id,
        "actor_name": row.actor_name,
        "action": a.action,
        "target_type": a.target_type,
        "target_id": a.target_id,
        "after_state": a.after_state or {},
        "created_at": a.created_at.isoformat(),
    }


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_workspace(
        self,
        workspace_id: int,
        *,
        before_id: int | None = None,
        action: str | None = None,
        actor_id: int | None = None,
        limit: int = 50,
    ) -> list[dict]:
        stmt = (
            select(AuditLog, User.name.label("actor_name"))
            .outerjoin(User, User.id == AuditLog.actor_id)
            .where(AuditLog.workspace_id == workspace_id)
        )
        if before_id is not None:
            stmt = stmt.where(AuditLog.id < before_id)
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if actor_id is not None:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
        stmt = stmt.order_by(AuditLog.id.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return [_to_api(row) for row in res.all()]
