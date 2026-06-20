from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        workspace_id: int,
        entity_type: str,
        entity_id: int,
        author_id: int | None,
        body: str,
        parent_id: int | None = None,
    ) -> Comment:
        row = Comment(
            workspace_id=workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            body=body,
            parent_id=parent_id,
        )
        self.session.add(row)
        await self.session.flush()
        # Refresh so the eager `author` relationship is populated for the response.
        await self.session.refresh(row)
        return row

    async def list_for_entity(
        self, entity_type: str, entity_id: int, *, limit: int = 200
    ) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(
                Comment.entity_type == entity_type,
                Comment.entity_id == entity_id,
                Comment.deleted_at.is_(None),
            )
            .order_by(Comment.id.asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get(self, comment_id: int) -> Comment | None:
        return await self.session.get(Comment, comment_id)

    async def update_body(self, comment: Comment, body: str) -> Comment:
        comment.body = body
        comment.edited_at = datetime.now(timezone.utc)
        await self.session.flush()
        return comment

    async def soft_delete(self, comment: Comment) -> None:
        comment.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
