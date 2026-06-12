from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, owner_id: int, name: str, description: str = "",
                     color: str = "#6366f1") -> Project:
        project = Project(owner_id=owner_id, name=name, description=description, color=color)
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def list_for_owner(self, owner_id: int, *, limit: int, offset: int) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_for_owner(self, project_id: int, owner_id: int) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update(self, project: Project, **fields) -> Project:
        for key, value in fields.items():
            if value is not None:
                setattr(project, key, value)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.commit()
