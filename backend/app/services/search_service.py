class SearchService:
    """Fans /search out across Postgres (projects, tasks) and MongoDB
    (snippets, bookmarks); each repo enforces owner scoping itself."""

    def __init__(self, project_repo, task_repo, snippet_repo, bookmark_repo) -> None:
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.snippet_repo = snippet_repo
        self.bookmark_repo = bookmark_repo

    async def search(self, *, owner_id: int, q: str, limit_per_group: int = 10) -> dict:
        return {
            "projects": await self.project_repo.search(owner_id, q, limit=limit_per_group),
            "tasks": await self.task_repo.search(owner_id, q, limit=limit_per_group),
            "snippets": await self.snippet_repo.search(owner_id=owner_id, q=q,
                                                       limit=limit_per_group),
            "bookmarks": await self.bookmark_repo.search(owner_id=owner_id, q=q,
                                                         limit=limit_per_group),
        }
