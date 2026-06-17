from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.events import emit
from app.models.project import Project
from app.models.workspace import Membership


class ProjectService:
    def __init__(self, session: AsyncSession, repo, task_repo=None,
                 snippet_repo=None, bookmark_repo=None) -> None:
        self.session = session
        self.repo = repo
        self.task_repo = task_repo
        self.snippet_repo = snippet_repo
        self.bookmark_repo = bookmark_repo

    async def create(self, *, workspace_id: int, owner_id: int, name: str,
                     description: str = "", color: str = "#6366f1"):
        project = await self.repo.create(
            workspace_id=workspace_id, owner_id=owner_id,
            name=name, description=description, color=color,
        )
        await emit(self.session, "project.created",
                   {"id": project.id, "name": project.name, "owner_id": owner_id},
                   workspace_id=workspace_id)
        await self.session.commit()
        return project

    async def list(self, workspace_id: int, *, limit: int = 50, offset: int = 0):
        return await self.repo.list_for_workspace(workspace_id, limit=limit, offset=offset)

    async def get(self, project_id: int, workspace_id: int):
        project = await self.repo.get_for_workspace(project_id, workspace_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    async def update(self, project_id: int, workspace_id: int, **fields):
        project = await self.get(project_id, workspace_id)
        updated = await self.repo.update(project, **fields)
        await emit(self.session, "project.updated",
                   {"id": project_id, **{k: v for k, v in fields.items() if v is not None}},
                   workspace_id=workspace_id)
        await self.session.commit()
        return updated

    async def delete(self, project_id: int, workspace_id: int) -> None:
        project = await self.get(project_id, workspace_id)
        await self.repo.delete(project)
        if self.snippet_repo is not None:
            await self.snippet_repo.detach_project(project_id)
        if self.bookmark_repo is not None:
            await self.bookmark_repo.detach_project(project_id)
        await emit(self.session, "project.deleted",
                   {"id": project_id}, workspace_id=workspace_id)
        await self.session.commit()

    async def summary(self, project_id: int, workspace_id: int) -> dict:
        await self.get(project_id, workspace_id)
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

    async def get_project_for_user(self, project_id: int, user_id: int):
        stmt = select(Project).where(Project.id == project_id)
        res = await self.session.execute(stmt)
        project = res.scalar_one_or_none()
        if project is None:
            raise NotFoundError("Project not found")

        # Verify active membership in project's workspace
        member_stmt = select(Membership).where(
            Membership.workspace_id == project.workspace_id,
            Membership.user_id == user_id,
            Membership.status == "active"
        )
        member_res = await self.session.execute(member_stmt)
        if member_res.scalar_one_or_none() is None:
            raise NotFoundError("Project not found")

        return project

    async def get_project_summary_for_user(self, project_id: int, user_id: int) -> dict:
        project = await self.get_project_for_user(project_id, user_id)
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
