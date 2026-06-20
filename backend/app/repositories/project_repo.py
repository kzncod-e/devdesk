import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.platform.search import rank, vector_match


def make_project_key(name: str) -> str:
    """A short identifier prefix from the name: initials for multi-word names,
    first 4 letters for a single word (e.g. "Acme Platform" → "AP", "Acme" → "ACME")."""
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "PRJ"
    if len(words) == 1:
        return words[0][:4].upper()
    return "".join(w[0] for w in words[:4]).upper()


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: int, owner_id: int, name: str,
                     description: str = "", color: str = "#6366f1") -> Project:
        project = Project(workspace_id=workspace_id, owner_id=owner_id, name=name,
                          key=make_project_key(name), description=description, color=color)
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def list_for_workspace(self, workspace_id: int, *, limit: int, offset: int) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.workspace_id == workspace_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_for_workspace(self, project_id: int, workspace_id: int) -> Project | None:
        stmt = select(Project).where(
            Project.id == project_id, Project.workspace_id == workspace_id
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def search(self, workspace_id: int, q: str, *, limit: int) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.workspace_id == workspace_id,
                   vector_match(self.session, "search_vector",
                                Project.name, Project.description, q=q))
            .order_by(rank(self.session, "search_vector", q=q).desc(), Project.id.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update(self, project: Project, **fields) -> Project:
        for key, value in fields.items():
            if value is not None:
                setattr(project, key, value)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()
