from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.repositories.project_repo import fts_clause


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, project_id: int, workspace_id: int, title: str,
                     position: float, description: str = "", priority: str = "medium",
                     due_date: date | None = None,
                     assignees: list[User] | None = None) -> Task:
        task = Task(project_id=project_id, workspace_id=workspace_id, title=title,
                    position=position, description=description, priority=priority,
                    due_date=due_date, assignees=assignees or [])
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def set_assignees(self, task: Task, users: list[User]) -> Task:
        task.assignees = users
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def list_for_project(self, project_id: int, *, limit: int, offset: int) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.project_id == project_id)
            .order_by(Task.position)
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_in_workspace(self, task_id: int, workspace_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.workspace_id == workspace_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def search(self, workspace_id: int, q: str, *, limit: int) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.workspace_id == workspace_id,
                   fts_clause(self.session, Task.title, Task.description, q=q))
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def max_position(self, project_id: int, status: str) -> float | None:
        stmt = select(func.max(Task.position)).where(
            Task.project_id == project_id, Task.status == status
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def count_by_status(self, project_id: int) -> dict[str, int]:
        stmt = (
            select(Task.status, func.count())
            .where(Task.project_id == project_id)
            .group_by(Task.status)
        )
        res = await self.session.execute(stmt)
        return {status: count for status, count in res.all()}

    async def update(self, task: Task, **fields) -> Task:
        for key, value in fields.items():
            if value is not None:
                setattr(task, key, value)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()
