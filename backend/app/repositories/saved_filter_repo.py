from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_filter import SavedFilter


def _to_api(f: SavedFilter) -> dict:
    return {
        "id": f.id,
        "name": f.name,
        "kind": f.kind,
        "query": f.query or {},
        "created_at": f.created_at.isoformat(),
    }


class SavedFilterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, user_id: int, workspace_id: int, name: str,
                     kind: str, query: dict) -> dict:
        row = SavedFilter(user_id=user_id, workspace_id=workspace_id, name=name,
                          kind=kind, query=query)
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return _to_api(row)

    async def list(self, *, user_id: int, workspace_id: int,
                   kind: str | None = None) -> list[dict]:
        stmt = select(SavedFilter).where(
            SavedFilter.user_id == user_id,
            SavedFilter.workspace_id == workspace_id,
        )
        if kind is not None:
            stmt = stmt.where(SavedFilter.kind == kind)
        stmt = stmt.order_by(SavedFilter.name)
        res = await self.session.execute(stmt)
        return [_to_api(f) for f in res.scalars().all()]

    async def get(self, filter_id: int, *, user_id: int) -> SavedFilter | None:
        f = await self.session.get(SavedFilter, filter_id)
        if f is None or f.user_id != user_id:
            return None
        return f

    async def delete(self, saved_filter: SavedFilter) -> None:
        await self.session.delete(saved_filter)
        await self.session.flush()
