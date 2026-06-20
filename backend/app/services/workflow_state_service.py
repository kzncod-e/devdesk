from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.repositories.workflow_state_repo import WorkflowStateRepository


class WorkflowStateService:
    def __init__(self, session: AsyncSession, repo: WorkflowStateRepository, project_repo) -> None:
        self.session = session
        self.repo = repo
        self.project_repo = project_repo

    async def _require_project(self, project_id: int, workspace_id: int):
        project = await self.project_repo.get_for_workspace(project_id, workspace_id)
        if project is None:
            raise NotFoundError("Project not found")

    async def list(self, project_id: int, workspace_id: int):
        await self._require_project(project_id, workspace_id)
        states = await self.repo.list_for_project(project_id)
        # Defensive: older projects with no states get the defaults on first read.
        if not states:
            await self.repo.seed_defaults(project_id)
            await self.session.commit()
            states = await self.repo.list_for_project(project_id)
        return states

    async def create(self, project_id: int, workspace_id: int, *, name: str,
                     category: str, color: str | None):
        await self._require_project(project_id, workspace_id)
        position = (await self.repo.max_position(project_id) or 0.0) + 1000.0
        state = await self.repo.create(project_id=project_id, name=name,
                                       category=category, position=position, color=color)
        await self.session.commit()
        return state

    async def update(self, state_id: int, project_id: int, workspace_id: int, **fields):
        await self._require_project(project_id, workspace_id)
        state = await self.repo.get_in_project(state_id, project_id)
        if state is None:
            raise NotFoundError("State not found")
        updated = await self.repo.update(state, **fields)
        await self.session.commit()
        return updated

    async def delete(self, state_id: int, project_id: int, workspace_id: int) -> None:
        await self._require_project(project_id, workspace_id)
        state = await self.repo.get_in_project(state_id, project_id)
        if state is None:
            raise NotFoundError("State not found")
        if await self.repo.count(project_id) <= 1:
            raise UnprocessableError("A project needs at least one column")
        if await self.repo.count_tasks(state_id) > 0:
            raise ConflictError("Move this column's tasks before deleting it")
        await self.repo.delete(state)
        await self.session.commit()
