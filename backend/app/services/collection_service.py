from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, UnprocessableError

_KINDS = ("snippet", "bookmark")


class CollectionService:
    def __init__(self, session: AsyncSession, repo) -> None:
        self.session = session
        self.repo = repo

    async def create(self, *, workspace_id: int, name: str, kind: str,
                     parent_id: int | None) -> dict:
        if kind not in _KINDS:
            raise UnprocessableError(f"Invalid collection kind: {kind}")
        if parent_id is not None:
            await self._require_parent(parent_id, workspace_id, kind)
        doc = await self.repo.create(workspace_id=workspace_id, name=name, kind=kind,
                                     parent_id=parent_id)
        await self.session.commit()
        return doc

    async def list(self, workspace_id: int, *, kind: str | None = None) -> list[dict]:
        return await self.repo.list(workspace_id, kind=kind)

    async def update(self, collection_id: int, workspace_id: int, *, name: str | None,
                     parent_id: int | None, set_parent: bool) -> dict:
        c = await self.repo.get(collection_id, workspace_id)
        if c is None:
            raise NotFoundError("Collection not found")
        fields: dict = {}
        if name is not None:
            fields["name"] = name
        if set_parent:
            if parent_id is not None:
                if parent_id == collection_id:
                    raise UnprocessableError("A collection cannot be its own parent")
                await self._require_parent(parent_id, workspace_id, c.kind)
            fields["parent_id"] = parent_id
        doc = await self.repo.update(c, **fields)
        await self.session.commit()
        return doc

    async def delete(self, collection_id: int, workspace_id: int) -> None:
        c = await self.repo.get(collection_id, workspace_id)
        if c is None:
            raise NotFoundError("Collection not found")
        await self.repo.delete(c)
        await self.session.commit()

    async def _require_parent(self, parent_id: int, workspace_id: int, kind: str) -> None:
        parent = await self.repo.get(parent_id, workspace_id)
        if parent is None:
            raise NotFoundError("Parent collection not found")
        if parent.kind != kind:
            raise UnprocessableError("Parent collection has a different kind")
