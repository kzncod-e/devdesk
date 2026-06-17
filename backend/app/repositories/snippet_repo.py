# annotations deferred: the `list` method would otherwise shadow the builtin
# when later return annotations (`-> list[dict]`) are evaluated in the class body.
from __future__ import annotations

from sqlalchemy import String, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.snippet import Snippet


def _to_api(s: Snippet) -> dict:
    return {
        "id": s.id,
        "project_id": s.project_id,
        "collection_id": s.collection_id,
        "title": s.title,
        "language": s.language,
        "code": s.code,
        "tags": list(s.tags or []),
        "notes": s.notes,
    }


def _is_pg(session: AsyncSession) -> bool:
    return session.bind.dialect.name == "postgresql"


def _tag_filter(session: AsyncSession, tag: str):
    if _is_pg(session):
        return Snippet.tags.any(tag)  # tag = ANY(tags)
    # SQLite test tier: tags are JSON text like ["api","db"].
    return func.cast(Snippet.tags, String).like(f'%"{tag}"%')


def _search_filter(session: AsyncSession, q: str):
    if _is_pg(session):
        doc = func.to_tsvector(
            "english",
            func.concat_ws(" ", Snippet.title, Snippet.code, Snippet.notes,
                           func.array_to_string(Snippet.tags, " ")),
        )
        return doc.op("@@")(func.websearch_to_tsquery("english", q))
    return or_(
        Snippet.title.ilike(f"%{q}%"),
        Snippet.code.ilike(f"%{q}%"),
        Snippet.notes.ilike(f"%{q}%"),
        func.cast(Snippet.tags, String).ilike(f"%{q}%"),
    )


class SnippetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: int, owner_id: int, title: str, language: str,
                     code: str, tags: list[str], notes: str, project_id: int | None,
                     collection_id: int | None = None) -> dict:
        s = Snippet(workspace_id=workspace_id, owner_id=owner_id, title=title,
                    language=language, code=code, tags=tags, notes=notes,
                    project_id=project_id, collection_id=collection_id)
        self.session.add(s)
        await self.session.flush()
        await self.session.refresh(s)
        return _to_api(s)

    async def list(self, *, workspace_id: int, project_id: int | None = None,
                   tag: str | None = None, language: str | None = None,
                   collection_id: int | None = None,
                   limit: int, offset: int) -> list[dict]:
        stmt = select(Snippet).where(Snippet.workspace_id == workspace_id)
        if project_id is not None:
            stmt = stmt.where(Snippet.project_id == project_id)
        if collection_id is not None:
            stmt = stmt.where(Snippet.collection_id == collection_id)
        if tag is not None:
            stmt = stmt.where(_tag_filter(self.session, tag))
        if language is not None:
            stmt = stmt.where(Snippet.language == language)
        stmt = stmt.order_by(Snippet.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return [_to_api(s) for s in res.scalars().all()]

    async def get(self, snippet_id: int, workspace_id: int) -> dict | None:
        s = await self._get(snippet_id, workspace_id)
        return _to_api(s) if s else None

    async def _get(self, snippet_id: int, workspace_id: int) -> Snippet | None:
        res = await self.session.execute(
            select(Snippet).where(Snippet.id == snippet_id,
                                  Snippet.workspace_id == workspace_id)
        )
        return res.scalar_one_or_none()

    async def update(self, snippet_id: int, workspace_id: int, *, fields: dict) -> dict | None:
        s = await self._get(snippet_id, workspace_id)
        if s is None:
            return None
        for key, value in fields.items():
            setattr(s, key, value)
        await self.session.flush()
        await self.session.refresh(s)
        return _to_api(s)

    async def delete(self, snippet_id: int, workspace_id: int) -> bool:
        s = await self._get(snippet_id, workspace_id)
        if s is None:
            return False
        await self.session.delete(s)
        await self.session.flush()
        return True

    async def search(self, *, workspace_id: int, q: str, limit: int) -> list[dict]:
        stmt = (
            select(Snippet)
            .where(Snippet.workspace_id == workspace_id, _search_filter(self.session, q))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return [_to_api(s) for s in res.scalars().all()]

    async def detach_project(self, project_id: int) -> None:
        await self.session.execute(
            update(Snippet).where(Snippet.project_id == project_id).values(project_id=None)
        )
        await self.session.flush()

    async def count_for_project(self, project_id: int) -> int:
        res = await self.session.execute(
            select(func.count()).select_from(Snippet).where(Snippet.project_id == project_id)
        )
        return int(res.scalar_one())
