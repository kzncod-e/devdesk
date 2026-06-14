from collections.abc import Awaitable, Callable

import httpx

from app.core.errors import NotFoundError
from app.core.htmlmeta import parse_metadata

FetchHtml = Callable[[str], Awaitable[str]]


async def default_fetch_html(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


class BookmarkService:
    def __init__(self, repo, project_repo, *, fetch_html: FetchHtml) -> None:
        self.repo = repo
        self.project_repo = project_repo
        self.fetch_html = fetch_html

    async def create(self, *, workspace_id: int, owner_id: int, url: str,
                     tags: list[str], project_id: int | None) -> dict:
        await self._validate_project(project_id, workspace_id)
        return await self.repo.create(workspace_id=workspace_id, owner_id=owner_id,
                                      url=url, tags=tags, project_id=project_id)

    async def list(self, *, workspace_id: int, project_id: int | None = None,
                   tag: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
        return await self.repo.list(workspace_id=workspace_id, project_id=project_id,
                                    tag=tag, limit=limit, offset=offset)

    async def get(self, bookmark_id: str, workspace_id: int) -> dict:
        doc = await self.repo.get(bookmark_id, workspace_id)
        if doc is None:
            raise NotFoundError("Bookmark not found")
        return doc

    async def update(self, bookmark_id: str, workspace_id: int, *, fields: dict) -> dict:
        if "project_id" in fields:
            await self._validate_project(fields["project_id"], workspace_id)
        doc = await self.repo.update(bookmark_id, workspace_id, fields=fields)
        if doc is None:
            raise NotFoundError("Bookmark not found")
        return doc

    async def delete(self, bookmark_id: str, workspace_id: int) -> None:
        if not await self.repo.delete(bookmark_id, workspace_id):
            raise NotFoundError("Bookmark not found")

    async def fetch_and_store_meta(self, bookmark_id: str, url: str) -> None:
        """Background task: scrape page metadata. Failures leave the doc as-is."""
        try:
            html = await self.fetch_html(url)
        except Exception:
            return
        meta = parse_metadata(html, url)
        await self.repo.set_metadata(
            bookmark_id,
            title=meta["title"],
            description=meta["description"],
            favicon=meta["favicon"],
            fetched_meta=meta,
        )

    async def _validate_project(self, project_id: int | None, workspace_id: int) -> None:
        if project_id is None:
            return
        if await self.project_repo.get_for_workspace(project_id, workspace_id) is None:
            raise NotFoundError("Project not found")
