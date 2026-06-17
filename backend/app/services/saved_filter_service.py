from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, UnprocessableError

_KINDS = ("snippet", "bookmark", "task", "project")


class SavedFilterService:
    def __init__(self, session: AsyncSession, repo) -> None:
        self.session = session
        self.repo = repo

    async def create(self, *, user_id: int, workspace_id: int, name: str,
                     kind: str, query: dict) -> dict:
        if kind not in _KINDS:
            raise UnprocessableError(f"Invalid filter kind: {kind}")
        doc = await self.repo.create(user_id=user_id, workspace_id=workspace_id,
                                     name=name, kind=kind, query=query)
        await self.session.commit()
        return doc

    async def list(self, *, user_id: int, workspace_id: int,
                   kind: str | None = None) -> list[dict]:
        return await self.repo.list(user_id=user_id, workspace_id=workspace_id, kind=kind)

    async def delete(self, filter_id: int, *, user_id: int) -> None:
        f = await self.repo.get(filter_id, user_id=user_id)
        if f is None:
            raise NotFoundError("Saved filter not found")
        await self.repo.delete(f)
        await self.session.commit()
