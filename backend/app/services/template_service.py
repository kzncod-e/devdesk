"""Capture existing content into reusable templates and instantiate them back.

Payload shapes
--------------
project: {
    "project": {"name", "description", "color"},
    "tasks":   [{"title", "description", "status", "priority"}],
    "snippets":[{"title", "language", "code", "tags", "notes"}],
}
snippet: {
    "snippet": {"title", "language", "code", "tags", "notes"},
}

Because projects, tasks and snippets all live in Postgres now, "use" runs as a
single transaction — a partial instantiation can never be committed.
"""
# Deferred annotations: this class defines a `list()` method, which would shadow
# the builtin `list` in later `-> list[dict]` return annotations (evaluated at
# class-body time) without this import.
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError, UnprocessableError
from app.core.events import emit

_KINDS = ("project", "snippet")
_VISIBILITIES = ("workspace", "public")
_CAPTURE_TASK_LIMIT = 200
_CAPTURE_SNIPPET_LIMIT = 200


class TemplateService:
    def __init__(self, session: AsyncSession, repo, project_repo, task_repo,
                 snippet_repo) -> None:
        self.session = session
        self.repo = repo
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.snippet_repo = snippet_repo

    # ── read ────────────────────────────────────────────────────────────────
    async def list(self, *, workspace_id: int, kind: str | None = None,
                   visibility: str | None = None) -> list[dict]:
        return await self.repo.list_available(
            workspace_id, kind=kind, visibility=visibility)

    async def gallery(self, *, kind: str | None = None, limit: int = 50) -> list[dict]:
        return await self.repo.list_gallery(kind=kind, limit=limit)

    async def get(self, template_id: int, *, workspace_id: int) -> dict:
        t = await self.repo.get(template_id)
        if t is None or not self._can_use(t, workspace_id):
            raise NotFoundError("Template not found")
        return _detail(t)

    # ── capture ──────────────────────────────────────────────────────────────
    async def capture(self, *, workspace_id: int, created_by: int, kind: str,
                      source_id: int, name: str, description: str,
                      visibility: str, can_publish: bool) -> dict:
        self._validate_kind(kind)
        self._validate_visibility(visibility, can_publish)

        if kind == "project":
            payload = await self._serialize_project(source_id, workspace_id)
        else:
            payload = await self._serialize_snippet(source_id, workspace_id)

        row = await self.repo.create(
            workspace_id=workspace_id, kind=kind, name=name, description=description,
            payload=payload, visibility=visibility, created_by=created_by,
        )
        await emit(self.session, "template.created",
                   {"id": row.id, "kind": kind, "name": name},
                   workspace_id=workspace_id)
        await self.session.commit()
        return _detail(row)

    async def create_from_payload(self, *, workspace_id: int, created_by: int,
                                  kind: str, name: str, description: str,
                                  payload: dict, visibility: str,
                                  can_publish: bool) -> dict:
        self._validate_kind(kind)
        self._validate_visibility(visibility, can_publish)
        row = await self.repo.create(
            workspace_id=workspace_id, kind=kind, name=name, description=description,
            payload=payload or {}, visibility=visibility, created_by=created_by,
        )
        await emit(self.session, "template.created",
                   {"id": row.id, "kind": kind, "name": name},
                   workspace_id=workspace_id)
        await self.session.commit()
        return _detail(row)

    # ── use (instantiate) ──────────────────────────────────────────────────
    async def use(self, template_id: int, *, workspace_id: int, owner_id: int) -> dict:
        t = await self.repo.get(template_id)
        if t is None or not self._can_use(t, workspace_id):
            raise NotFoundError("Template not found")

        if t.kind == "project":
            ref = await self._instantiate_project(t.payload or {}, workspace_id, owner_id)
        else:
            ref = await self._instantiate_snippet(t.payload or {}, workspace_id, owner_id)

        await self.repo.increment_use_count(t.id)
        await emit(self.session, "template.used",
                   {"id": t.id, "kind": t.kind, "name": t.name, **ref},
                   workspace_id=workspace_id)
        await self.session.commit()
        return {"kind": t.kind, **ref}

    async def delete(self, template_id: int, *, workspace_id: int) -> None:
        t = await self.repo.get(template_id)
        if t is None:
            raise NotFoundError("Template not found")
        # Only a workspace's own templates are deletable; globals are system-owned.
        if t.workspace_id != workspace_id:
            raise ForbiddenError("Cannot delete a template you don't own")
        await self.repo.delete(t)
        await self.session.commit()

    # ── serialization ─────────────────────────────────────────────────────────
    async def _serialize_project(self, project_id: int, workspace_id: int) -> dict:
        project = await self.project_repo.get_for_workspace(project_id, workspace_id)
        if project is None:
            raise NotFoundError("Project not found")
        tasks = await self.task_repo.list_for_project(
            project_id, limit=_CAPTURE_TASK_LIMIT, offset=0)
        snippets = await self.snippet_repo.list(
            workspace_id=workspace_id, project_id=project_id,
            limit=_CAPTURE_SNIPPET_LIMIT, offset=0)
        return {
            "project": {
                "name": project.name,
                "description": project.description,
                "color": project.color,
            },
            "tasks": [
                {"title": t.title, "description": t.description,
                 "status": t.status, "priority": t.priority}
                for t in tasks
            ],
            "snippets": [
                {"title": s["title"], "language": s["language"], "code": s["code"],
                 "tags": s.get("tags", []), "notes": s.get("notes", "")}
                for s in snippets
            ],
        }

    async def _serialize_snippet(self, snippet_id: int, workspace_id: int) -> dict:
        doc = await self.snippet_repo.get(snippet_id, workspace_id)
        if doc is None:
            raise NotFoundError("Snippet not found")
        return {
            "snippet": {
                "title": doc["title"], "language": doc["language"], "code": doc["code"],
                "tags": doc.get("tags", []), "notes": doc.get("notes", ""),
            }
        }

    # ── instantiation ─────────────────────────────────────────────────────────
    async def _instantiate_project(self, payload: dict, workspace_id: int,
                                   owner_id: int) -> dict:
        meta = payload.get("project") or {}
        project = await self.project_repo.create(
            workspace_id=workspace_id, owner_id=owner_id,
            name=meta.get("name") or "Untitled project",
            description=meta.get("description", ""),
            color=meta.get("color", "#6366f1"),
        )
        await emit(self.session, "project.created",
                   {"id": project.id, "name": project.name, "owner_id": owner_id},
                   workspace_id=workspace_id)

        for i, t in enumerate(payload.get("tasks") or []):
            task = await self.task_repo.create(
                project_id=project.id, workspace_id=workspace_id,
                title=t.get("title") or "Untitled task",
                description=t.get("description", ""),
                priority=t.get("priority", "medium"),
                position=(i + 1) * 1000.0,
            )
            status = t.get("status")
            if status in ("todo", "in_progress", "done"):
                task.status = status

        for s in payload.get("snippets") or []:
            await self.snippet_repo.create(
                workspace_id=workspace_id, owner_id=owner_id,
                title=s.get("title") or "Untitled snippet",
                language=s.get("language", "text"),
                code=s.get("code", ""), tags=s.get("tags", []),
                notes=s.get("notes", ""), project_id=project.id,
            )

        return {"project_id": project.id}

    async def _instantiate_snippet(self, payload: dict, workspace_id: int,
                                  owner_id: int) -> dict:
        s = payload.get("snippet") or {}
        doc = await self.snippet_repo.create(
            workspace_id=workspace_id, owner_id=owner_id,
            title=s.get("title") or "Untitled snippet",
            language=s.get("language", "text"),
            code=s.get("code", ""), tags=s.get("tags", []),
            notes=s.get("notes", ""), project_id=None,
        )
        await emit(self.session, "snippet.created",
                   {"id": doc["id"], "title": doc["title"], "language": doc["language"]},
                   workspace_id=workspace_id)
        return {"snippet_id": doc["id"]}

    # ── helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _can_use(t, workspace_id: int) -> bool:
        return (t.workspace_id == workspace_id
                or t.workspace_id is None
                or t.visibility == "public")

    @staticmethod
    def _validate_kind(kind: str) -> None:
        if kind not in _KINDS:
            raise UnprocessableError(f"Invalid template kind: {kind}")

    @staticmethod
    def _validate_visibility(visibility: str, can_publish: bool) -> None:
        if visibility not in _VISIBILITIES:
            raise UnprocessableError(f"Invalid visibility: {visibility}")
        if visibility == "public" and not can_publish:
            raise ForbiddenError("Publishing public templates requires workspace:manage")


def _detail(t) -> dict:
    return {
        "id": t.id,
        "workspace_id": t.workspace_id,
        "kind": t.kind,
        "name": t.name,
        "description": t.description,
        "visibility": t.visibility,
        "created_by": t.created_by,
        "use_count": t.use_count,
        "created_at": t.created_at.isoformat(),
        "payload": t.payload or {},
    }
