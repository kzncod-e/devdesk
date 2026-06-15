from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.user import User


def _to_api(row) -> dict:
    a: Activity = row.Activity
    return {
        "id": a.id,
        "workspace_id": a.workspace_id,
        "actor_id": a.actor_id,
        "actor_name": row.actor_name,
        "verb": a.verb,
        "entity_type": a.entity_type,
        "entity_id": a.entity_id,
        "entity_name": a.entity_name,
        "metadata": a.meta or {},
        "created_at": a.created_at.isoformat(),
    }


class ActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_workspace(
        self,
        workspace_id: int,
        *,
        before_id: int | None = None,
        limit: int = 30,
    ) -> list[dict]:
        stmt = (
            select(Activity, User.name.label("actor_name"))
            .outerjoin(User, User.id == Activity.actor_id)
            .where(Activity.workspace_id == workspace_id)
        )
        if before_id is not None:
            stmt = stmt.where(Activity.id < before_id)
        stmt = stmt.order_by(Activity.id.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return [_to_api(row) for row in res.all()]
