class SearchService:
    """Fans /search out across Postgres (projects, tasks) and MongoDB
    (snippets, bookmarks); every repo is scoped to the active workspace."""

    def __init__(self, project_repo, task_repo, snippet_repo, bookmark_repo) -> None:
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.snippet_repo = snippet_repo
        self.bookmark_repo = bookmark_repo

    async def search(self, *, workspace_id: int, q: str, limit_per_group: int = 10) -> dict:
        return {
            "projects": await self.project_repo.search(workspace_id, q, limit=limit_per_group),
            "tasks": await self.task_repo.search(workspace_id, q, limit=limit_per_group),
            "snippets": await self.snippet_repo.search(workspace_id=workspace_id, q=q,
                                                       limit=limit_per_group),
            "bookmarks": await self.bookmark_repo.search(workspace_id=workspace_id, q=q,
                                                         limit=limit_per_group),
        }
