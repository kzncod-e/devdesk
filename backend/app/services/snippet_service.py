from app.core.errors import NotFoundError


class SnippetService:
    def __init__(self, repo, project_repo) -> None:
        self.repo = repo
        self.project_repo = project_repo

    async def create(self, *, owner_id: int, title: str, language: str, code: str,
                     tags: list[str], notes: str, project_id: int | None) -> dict:
        await self._validate_project(project_id, owner_id)
        return await self.repo.create(owner_id=owner_id, title=title, language=language,
                                      code=code, tags=tags, notes=notes,
                                      project_id=project_id)

    async def list(self, *, owner_id: int, project_id: int | None = None,
                   tag: str | None = None, language: str | None = None,
                   limit: int = 50, offset: int = 0) -> list[dict]:
        return await self.repo.list(owner_id=owner_id, project_id=project_id, tag=tag,
                                    language=language, limit=limit, offset=offset)

    async def get(self, snippet_id: str, owner_id: int) -> dict:
        doc = await self.repo.get(snippet_id, owner_id)
        if doc is None:
            raise NotFoundError("Snippet not found")
        return doc

    async def update(self, snippet_id: str, owner_id: int, *, fields: dict) -> dict:
        if "project_id" in fields:
            await self._validate_project(fields["project_id"], owner_id)
        doc = await self.repo.update(snippet_id, owner_id, fields=fields)
        if doc is None:
            raise NotFoundError("Snippet not found")
        return doc

    async def delete(self, snippet_id: str, owner_id: int) -> None:
        if not await self.repo.delete(snippet_id, owner_id):
            raise NotFoundError("Snippet not found")

    async def _validate_project(self, project_id: int | None, owner_id: int) -> None:
        # cross-database reference check: Mongo docs may only point at the
        # owner's own Postgres projects
        if project_id is None:
            return
        if await self.project_repo.get_for_owner(project_id, owner_id) is None:
            raise NotFoundError("Project not found")
