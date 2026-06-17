from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.events import emit
from app.models.task import Task
from app.models.workspace import Membership

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
        await emit(
            self.session,
            "task.created",
            {
                "id": task.id,
                "project_id": project_id,
                "title": title,
                "assignee_ids": [u.id for u in assignees],
            },
            workspace_id=workspace_id,
        )
        await self.session.commit()
        return task

    async def set_assignees(self, task_id: int, workspace_id: int, user_ids: list[int]):
        task = await self._require_task(task_id, workspace_id)
        old_ids = {u.id for u in task.assignees}
        users = await self.user_repo.get_by_ids(user_ids)
        updated = await self.task_repo.set_assignees(task, users)
        added = [uid for uid in user_ids if uid not in old_ids]
        await emit(
            self.session,
            "task.assignees_changed",
            {
                "id": task_id,
                "user_ids": user_ids,
                "added_user_ids": added,
                "title": task.title,
                "project_id": task.project_id,
            },
            workspace_id=workspace_id,
        )
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

    async def get(self, task_id: int, workspace_id: int):
        return await self._require_task(task_id, workspace_id)

    async def get_task_for_user(self, task_id: int, user_id: int):
        stmt = select(Task).where(Task.id == task_id)
        res = await self.session.execute(stmt)
        task = res.scalar_one_or_none()
        if task is None:
            raise NotFoundError("Task not found")

        # Verify the user has active membership in this task's workspace
        member_stmt = select(Membership).where(
            Membership.workspace_id == task.workspace_id,
            Membership.user_id == user_id,
            Membership.status == "active"
        )
        member_res = await self.session.execute(member_stmt)
        if member_res.scalar_one_or_none() is None:
            raise NotFoundError("Task not found")

        return task

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
