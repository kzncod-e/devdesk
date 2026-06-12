from app.core.errors import NotFoundError


class ProjectService:
    def __init__(self, repo, task_repo=None, snippet_repo=None, bookmark_repo=None) -> None:
        self.repo = repo
        self.task_repo = task_repo
        self.snippet_repo = snippet_repo
        self.bookmark_repo = bookmark_repo

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
        # detach (not delete) associated Mongo docs so general-purpose value
        # isn't lost — spec §2 decision
        if self.snippet_repo is not None:
            await self.snippet_repo.detach_project(project_id)
        if self.bookmark_repo is not None:
            await self.bookmark_repo.detach_project(project_id)

    async def summary(self, project_id: int, owner_id: int) -> dict:
        await self.get(project_id, owner_id)
        counts = await self.task_repo.count_by_status(project_id)
        tasks = {
            "todo": counts.get("todo", 0),
            "in_progress": counts.get("in_progress", 0),
            "done": counts.get("done", 0),
        }
        tasks["total"] = sum(tasks.values())
        snippets = (await self.snippet_repo.count_for_project(project_id)
                    if self.snippet_repo is not None else 0)
        bookmarks = (await self.bookmark_repo.count_for_project(project_id)
                     if self.bookmark_repo is not None else 0)
        return {"tasks": tasks, "snippets": snippets, "bookmarks": bookmarks}
