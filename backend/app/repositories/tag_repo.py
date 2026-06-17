from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


def _to_api(t: Tag) -> dict:
    return {"id": t.id, "name": t.name, "color": t.color}


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, workspace_id: int) -> list[dict]:
        stmt = (select(Tag).where(Tag.workspace_id == workspace_id)
                .order_by(Tag.name))
        res = await self.session.execute(stmt)
        return [_to_api(t) for t in res.scalars().all()]

    async def get(self, tag_id: int, workspace_id: int) -> Tag | None:
        t = await self.session.get(Tag, tag_id)
        if t is None or t.workspace_id != workspace_id:
            return None
        return t

    async def sync(self, workspace_id: int, names: list[str]) -> None:
        """Insert any tag names not yet in the registry (default color). Cross-dialect
        (no ON CONFLICT): selects existing names, inserts the difference."""
        wanted = {n.strip() for n in names if n and n.strip()}
        if not wanted:
            return
        existing = await self.session.execute(
            select(Tag.name).where(Tag.workspace_id == workspace_id,
                                   Tag.name.in_(wanted))
        )
        have = {row[0] for row in existing.all()}
        for name in wanted - have:
            self.session.add(Tag(workspace_id=workspace_id, name=name))
        await self.session.flush()

    async def update_color(self, tag: Tag, color: str) -> dict:
        tag.color = color
        await self.session.flush()
        return _to_api(tag)

    async def delete(self, tag: Tag) -> None:
        await self.session.delete(tag)
        await self.session.flush()
