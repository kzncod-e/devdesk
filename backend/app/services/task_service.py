from datetime import date

from app.core.errors import NotFoundError

POSITION_STEP = 1024.0


class TaskService:
    def __init__(self, task_repo, project_repo) -> None:
        self.task_repo = task_repo
        self.project_repo = project_repo

    async def create(self, *, owner_id: int, project_id: int, title: str,
                     description: str = "", priority: str = "medium",
                     due_date: date | None = None):
        await self._require_project(project_id, owner_id)
        max_pos = await self.task_repo.max_position(project_id, "todo")
        position = (max_pos or 0.0) + POSITION_STEP
        return await self.task_repo.create(
            project_id=project_id, title=title, position=position,
            description=description, priority=priority, due_date=due_date,
        )

    async def list(self, *, owner_id: int, project_id: int,
                   limit: int = 200, offset: int = 0):
        await self._require_project(project_id, owner_id)
        return await self.task_repo.list_for_project(project_id, limit=limit, offset=offset)

    async def update(self, task_id: int, owner_id: int, **fields):
        task = await self._require_task(task_id, owner_id)
        return await self.task_repo.update(task, **fields)

    async def delete(self, task_id: int, owner_id: int) -> None:
        task = await self._require_task(task_id, owner_id)
        await self.task_repo.delete(task)

    async def _require_project(self, project_id: int, owner_id: int):
        project = await self.project_repo.get_for_owner(project_id, owner_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    async def _require_task(self, task_id: int, owner_id: int):
        task = await self.task_repo.get_with_owner(task_id, owner_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task
