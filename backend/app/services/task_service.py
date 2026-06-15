from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.events import emit

POSITION_STEP = 1024.0


class TaskService:
    def __init__(self, session: AsyncSession, task_repo, project_repo, user_repo) -> None:
        self.session = session
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.user_repo = user_repo

    async def create(self, *, workspace_id: int, project_id: int, title: str,
                     description: str = "", priority: str = "medium",
                     due_date: date | None = None,
                     assignee_ids: list[int] | None = None):
        await self._require_project(project_id, workspace_id)
        max_pos = await self.task_repo.max_position(project_id, "todo")
        position = (max_pos or 0.0) + POSITION_STEP
        assignees = await self.user_repo.get_by_ids(assignee_ids or [])
        task = await self.task_repo.create(
            project_id=project_id, workspace_id=workspace_id, title=title,
            position=position, description=description, priority=priority,
            due_date=due_date, assignees=assignees,
        )
        await emit(self.session, "task.created",
                   {"id": task.id, "project_id": project_id, "title": title},
                   workspace_id=workspace_id)
        await self.session.commit()
        return task

    async def set_assignees(self, task_id: int, workspace_id: int, user_ids: list[int]):
        task = await self._require_task(task_id, workspace_id)
        users = await self.user_repo.get_by_ids(user_ids)
        updated = await self.task_repo.set_assignees(task, users)
        await emit(self.session, "task.assignees_changed",
                   {"id": task_id, "user_ids": user_ids}, workspace_id=workspace_id)
        await self.session.commit()
        return updated

    async def list(self, *, workspace_id: int, project_id: int,
                   limit: int = 200, offset: int = 0):
        await self._require_project(project_id, workspace_id)
        return await self.task_repo.list_for_project(project_id, limit=limit, offset=offset)

    async def update(self, task_id: int, workspace_id: int, **fields):
        task = await self._require_task(task_id, workspace_id)
        updated = await self.task_repo.update(task, **fields)
        payload: dict = {"id": task_id, **{k: v for k, v in fields.items() if v is not None}}
        topic = "task.status_changed" if "status" in fields else "task.updated"
        await emit(self.session, topic, payload, workspace_id=workspace_id)
        await self.session.commit()
        return updated

    async def delete(self, task_id: int, workspace_id: int) -> None:
        task = await self._require_task(task_id, workspace_id)
        await self.task_repo.delete(task)
        await emit(self.session, "task.deleted",
                   {"id": task_id}, workspace_id=workspace_id)
        await self.session.commit()

    async def _require_project(self, project_id: int, workspace_id: int):
        project = await self.project_repo.get_for_workspace(project_id, workspace_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    async def _require_task(self, task_id: int, workspace_id: int):
        task = await self.task_repo.get_in_workspace(task_id, workspace_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task
