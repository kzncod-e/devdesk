from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError


class TagService:
    def __init__(self, session: AsyncSession, repo) -> None:
        self.session = session
        self.repo = repo

    async def list(self, workspace_id: int) -> list[dict]:
        return await self.repo.list(workspace_id)

    async def set_color(self, tag_id: int, workspace_id: int, *, color: str) -> dict:
        tag = await self.repo.get(tag_id, workspace_id)
        if tag is None:
            raise NotFoundError("Tag not found")
        doc = await self.repo.update_color(tag, color)
        await self.session.commit()
        return doc

    async def delete(self, tag_id: int, workspace_id: int) -> None:
        tag = await self.repo.get(tag_id, workspace_id)
        if tag is None:
            raise NotFoundError("Tag not found")
        await self.repo.delete(tag)
        await self.session.commit()
