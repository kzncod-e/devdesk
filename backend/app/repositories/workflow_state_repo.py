from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.workflow_state import DEFAULT_STATES, WorkflowState


class WorkflowStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_project(self, project_id: int) -> list[WorkflowState]:
        stmt = (
            select(WorkflowState)
            .where(WorkflowState.project_id == project_id)
            .order_by(WorkflowState.position, WorkflowState.id)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_in_project(self, state_id: int, project_id: int) -> WorkflowState | None:
        state = await self.session.get(WorkflowState, state_id)
        return state if state and state.project_id == project_id else None

    async def first_for_project(self, project_id: int) -> WorkflowState | None:
        stmt = (
            select(WorkflowState)
            .where(WorkflowState.project_id == project_id)
            .order_by(WorkflowState.position)
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def find_by_category(self, project_id: int, category: str) -> WorkflowState | None:
        stmt = (
            select(WorkflowState)
            .where(WorkflowState.project_id == project_id, WorkflowState.category == category)
            .order_by(WorkflowState.position)
            .limit(1)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def create(self, *, project_id: int, name: str, category: str,
                     position: float, color: str | None = None) -> WorkflowState:
        state = WorkflowState(project_id=project_id, name=name, category=category,
                              position=position, color=color)
        self.session.add(state)
        await self.session.flush()
        await self.session.refresh(state)
        return state

    async def max_position(self, project_id: int) -> float | None:
        res = await self.session.execute(
            select(func.max(WorkflowState.position)).where(WorkflowState.project_id == project_id)
        )
        return res.scalar_one_or_none()

    async def count(self, project_id: int) -> int:
        res = await self.session.execute(
            select(func.count()).select_from(WorkflowState).where(
                WorkflowState.project_id == project_id)
        )
        return int(res.scalar_one())

    async def count_tasks(self, state_id: int) -> int:
        res = await self.session.execute(
            select(func.count()).select_from(Task).where(Task.state_id == state_id)
        )
        return int(res.scalar_one())

    async def update(self, state: WorkflowState, **fields) -> WorkflowState:
        for key, value in fields.items():
            if value is not None:
                setattr(state, key, value)
        await self.session.flush()
        return state

    async def delete(self, state: WorkflowState) -> None:
        await self.session.delete(state)
        await self.session.flush()

    async def seed_defaults(self, project_id: int) -> None:
        for d in DEFAULT_STATES:
            self.session.add(WorkflowState(project_id=project_id, **d))
        await self.session.flush()
