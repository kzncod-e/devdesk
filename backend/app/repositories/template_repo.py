from __future__ import annotations

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template


def _to_api(t: Template, *, include_payload: bool = False) -> dict:
    out = {
        "id": t.id,
        "workspace_id": t.workspace_id,
        "kind": t.kind,
        "name": t.name,
        "description": t.description,
        "visibility": t.visibility,
        "created_by": t.created_by,
        "use_count": t.use_count,
        "created_at": t.created_at.isoformat(),
    }
    if include_payload:
        out["payload"] = t.payload or {}
    return out


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, workspace_id: int | None, kind: str, name: str,
                     description: str, payload: dict, visibility: str,
                     created_by: int | None) -> Template:
        row = Template(
            workspace_id=workspace_id, kind=kind, name=name, description=description,
            payload=payload, visibility=visibility, created_by=created_by,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return row

    async def get(self, template_id: int) -> Template | None:
        return await self.session.get(Template, template_id)

    async def list_available(self, workspace_id: int, *, kind: str | None = None,
                             visibility: str | None = None) -> list[dict]:
        """Templates a workspace can use: its own, plus global (workspace_id NULL),
        plus any public template."""
        stmt = select(Template).where(
            or_(
                Template.workspace_id == workspace_id,
                Template.workspace_id.is_(None),
                Template.visibility == "public",
            )
        )
        if kind is not None:
            stmt = stmt.where(Template.kind == kind)
        if visibility is not None:
            stmt = stmt.where(Template.visibility == visibility)
        stmt = stmt.order_by(Template.use_count.desc(), Template.id.desc())
        res = await self.session.execute(stmt)
        return [_to_api(t) for t in res.scalars().all()]

    async def list_gallery(self, *, kind: str | None = None, limit: int = 50) -> list[dict]:
        """Public templates for the unauthenticated gallery, most-used first."""
        stmt = select(Template).where(Template.visibility == "public")
        if kind is not None:
            stmt = stmt.where(Template.kind == kind)
        stmt = stmt.order_by(Template.use_count.desc(), Template.id.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return [_to_api(t) for t in res.scalars().all()]

    async def delete(self, template: Template) -> None:
        await self.session.delete(template)
        await self.session.flush()

    async def increment_use_count(self, template_id: int) -> None:
        await self.session.execute(
            update(Template)
            .where(Template.id == template_id)
            .values(use_count=Template.use_count + 1)
        )
