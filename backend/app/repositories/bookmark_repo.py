# annotations deferred: the `list` method would otherwise shadow the builtin
# when later return annotations (`-> list[dict]`) are evaluated in the class body.
from __future__ import annotations

from sqlalchemy import String, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bookmark import Bookmark


def _to_api(b: Bookmark) -> dict:
    return {
        "id": b.id,
        "project_id": b.project_id,
        "url": b.url,
        "title": b.title,
        "description": b.description,
        "tags": list(b.tags or []),
        "favicon": b.favicon,
        "fetched_meta": b.fetched_meta or {},
    }


def _is_pg(session: AsyncSession) -> bool:
    return session.bind.dialect.name == "postgresql"


def _tag_filter(session: AsyncSession, tag: str):
    if _is_pg(session):
        return Bookmark.tags.any(tag)  # tag = ANY(tags)
    return func.cast(Bookmark.tags, String).like(f'%"{tag}"%')


def _search_filter(session: AsyncSession, q: str):
    if _is_pg(session):
        doc = func.to_tsvector(
            "english",
            func.concat_ws(" ", Bookmark.title, Bookmark.description, Bookmark.url,
                           func.array_to_string(Bookmark.tags, " ")),
        )
        return doc.op("@@")(func.websearch_to_tsquery("english", q))
    return or_(
        Bookmark.title.ilike(f"%{q}%"),
        Bookmark.description.ilike(f"%{q}%"),
        Bookmark.url.ilike(f"%{q}%"),
        func.cast(Bookmark.tags, String).ilike(f"%{q}%"),
    )


class BookmarkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: int, owner_id: int, url: str,
                     tags: list[str], project_id: int | None) -> dict:
        b = Bookmark(workspace_id=workspace_id, owner_id=owner_id, url=url,
                     tags=tags, project_id=project_id)
        self.session.add(b)
        await self.session.flush()
        await self.session.refresh(b)
        return _to_api(b)

    async def list(self, *, workspace_id: int, project_id: int | None = None,
                   tag: str | None = None, limit: int, offset: int) -> list[dict]:
        stmt = select(Bookmark).where(Bookmark.workspace_id == workspace_id)
        if project_id is not None:
            stmt = stmt.where(Bookmark.project_id == project_id)
        if tag is not None:
            stmt = stmt.where(_tag_filter(self.session, tag))
        stmt = stmt.order_by(Bookmark.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return [_to_api(b) for b in res.scalars().all()]

    async def get(self, bookmark_id: int, workspace_id: int) -> dict | None:
        b = await self._get(bookmark_id, workspace_id)
        return _to_api(b) if b else None

    async def _get(self, bookmark_id: int, workspace_id: int) -> Bookmark | None:
        res = await self.session.execute(
            select(Bookmark).where(Bookmark.id == bookmark_id,
                                   Bookmark.workspace_id == workspace_id)
        )
        return res.scalar_one_or_none()

    async def update(self, bookmark_id: int, workspace_id: int, *, fields: dict) -> dict | None:
        b = await self._get(bookmark_id, workspace_id)
        if b is None:
            return None
        for key, value in fields.items():
            setattr(b, key, value)
        await self.session.flush()
        await self.session.refresh(b)
        return _to_api(b)

    async def set_metadata(self, bookmark_id: int, *, title: str, description: str,
                           favicon: str, fetched_meta: dict) -> dict | None:
        res = await self.session.execute(select(Bookmark).where(Bookmark.id == bookmark_id))
        b = res.scalar_one_or_none()
        if b is None:
            return None
        b.title, b.description, b.favicon, b.fetched_meta = title, description, favicon, fetched_meta
        await self.session.commit()
        await self.session.refresh(b)
        return _to_api(b)

    async def delete(self, bookmark_id: int, workspace_id: int) -> bool:
        b = await self._get(bookmark_id, workspace_id)
        if b is None:
            return False
        await self.session.delete(b)
        await self.session.flush()
        return True

    async def search(self, *, workspace_id: int, q: str, limit: int) -> list[dict]:
        stmt = (
            select(Bookmark)
            .where(Bookmark.workspace_id == workspace_id, _search_filter(self.session, q))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return [_to_api(b) for b in res.scalars().all()]

    async def detach_project(self, project_id: int) -> None:
        await self.session.execute(
            update(Bookmark).where(Bookmark.project_id == project_id).values(project_id=None)
        )
        await self.session.flush()

    async def count_for_project(self, project_id: int) -> int:
        res = await self.session.execute(
            select(func.count()).select_from(Bookmark).where(Bookmark.project_id == project_id)
        )
        return int(res.scalar_one())
