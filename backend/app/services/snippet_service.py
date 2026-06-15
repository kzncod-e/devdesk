from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.events import emit


class SnippetService:
    def __init__(self, session: AsyncSession, repo, project_repo) -> None:
        self.session = session
        self.repo = repo
        self.project_repo = project_repo

    async def create(self, *, workspace_id: int, owner_id: int, title: str, language: str,
                     code: str, tags: list[str], notes: str, project_id: int | None) -> dict:
        await self._validate_project(project_id, workspace_id)
        doc = await self.repo.create(workspace_id=workspace_id, owner_id=owner_id,
                                     title=title, language=language, code=code,
                                     tags=tags, notes=notes, project_id=project_id)
        await emit(self.session, "snippet.created",
                   {"id": doc["id"], "title": title, "language": language},
                   workspace_id=workspace_id)
        await self.session.commit()
        return doc

    async def list(self, *, workspace_id: int, project_id: int | None = None,
                   tag: str | None = None, language: str | None = None,
                   limit: int = 50, offset: int = 0) -> list[dict]:
        return await self.repo.list(workspace_id=workspace_id, project_id=project_id,
                                    tag=tag, language=language, limit=limit, offset=offset)

    async def get(self, snippet_id: int, workspace_id: int) -> dict:
        doc = await self.repo.get(snippet_id, workspace_id)
        if doc is None:
            raise NotFoundError("Snippet not found")
        return doc

    async def update(self, snippet_id: int, workspace_id: int, *, fields: dict) -> dict:
        if "project_id" in fields:
            await self._validate_project(fields["project_id"], workspace_id)
        doc = await self.repo.update(snippet_id, workspace_id, fields=fields)
        if doc is None:
            raise NotFoundError("Snippet not found")
        await emit(self.session, "snippet.updated",
                   {"id": snippet_id, **fields}, workspace_id=workspace_id)
        await self.session.commit()
        return doc

    async def delete(self, snippet_id: int, workspace_id: int) -> None:
        if not await self.repo.delete(snippet_id, workspace_id):
            raise NotFoundError("Snippet not found")
        await emit(self.session, "snippet.deleted",
                   {"id": snippet_id}, workspace_id=workspace_id)
        await self.session.commit()

    async def _validate_project(self, project_id: int | None, workspace_id: int) -> None:
        if project_id is None:
            return
        if await self.project_repo.get_for_workspace(project_id, workspace_id) is None:
            raise NotFoundError("Project not found")
