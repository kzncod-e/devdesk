from app.core.errors import NotFoundError


class ProjectService:
    def __init__(self, repo) -> None:
        self.repo = repo

    async def create(self, *, owner_id: int, name: str, description: str = "",
                     color: str = "#6366f1"):
        return await self.repo.create(owner_id=owner_id, name=name,
                                      description=description, color=color)

    async def list(self, owner_id: int, *, limit: int = 50, offset: int = 0):
        return await self.repo.list_for_owner(owner_id, limit=limit, offset=offset)

    async def get(self, project_id: int, owner_id: int):
        project = await self.repo.get_for_owner(project_id, owner_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    async def update(self, project_id: int, owner_id: int, **fields):
        project = await self.get(project_id, owner_id)
        return await self.repo.update(project, **fields)

    async def delete(self, project_id: int, owner_id: int) -> None:
        project = await self.get(project_id, owner_id)
        await self.repo.delete(project)
