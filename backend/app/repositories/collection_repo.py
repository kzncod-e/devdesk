from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection


def _to_api(c: Collection) -> dict:
    return {
        "id": c.id,
        "workspace_id": c.workspace_id,
        "name": c.name,
        "kind": c.kind,
        "parent_id": c.parent_id,
    }


class CollectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: int, name: str, kind: str,
                     parent_id: int | None) -> dict:
        row = Collection(workspace_id=workspace_id, name=name, kind=kind,
                         parent_id=parent_id)
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return _to_api(row)

    async def get(self, collection_id: int, workspace_id: int) -> Collection | None:
        c = await self.session.get(Collection, collection_id)
        if c is None or c.workspace_id != workspace_id:
            return None
        return c

    async def list(self, workspace_id: int, *, kind: str | None = None) -> list[dict]:
        stmt = select(Collection).where(Collection.workspace_id == workspace_id)
        if kind is not None:
            stmt = stmt.where(Collection.kind == kind)
        stmt = stmt.order_by(Collection.name)
        res = await self.session.execute(stmt)
        return [_to_api(c) for c in res.scalars().all()]

    async def update(self, collection: Collection, **fields) -> dict:
        for k, v in fields.items():
            if v is not None or k == "parent_id":  # parent_id can be set to None
                setattr(collection, k, v)
        await self.session.flush()
        await self.session.refresh(collection)
        return _to_api(collection)

    async def delete(self, collection: Collection) -> None:
        await self.session.delete(collection)
        await self.session.flush()
