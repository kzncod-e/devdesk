class SearchService:
    """Fans /search out across Postgres (projects, tasks) and MongoDB
    (snippets, bookmarks); every repo is scoped to the active workspace."""

    def __init__(self, project_repo, task_repo, snippet_repo, bookmark_repo) -> None:
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.snippet_repo = snippet_repo
        self.bookmark_repo = bookmark_repo

    _ALL_TYPES = ("projects", "tasks", "snippets", "bookmarks")

    async def search(self, *, workspace_id: int, q: str, limit_per_group: int = 10,
                     types: set[str] | None = None) -> dict:
        want = types & set(self._ALL_TYPES) if types else set(self._ALL_TYPES)
        out: dict[str, list] = {t: [] for t in self._ALL_TYPES}

        if "projects" in want:
            out["projects"] = await self.project_repo.search(
                workspace_id, q, limit=limit_per_group)
        if "tasks" in want:
            out["tasks"] = await self.task_repo.search(
                workspace_id, q, limit=limit_per_group)
        if "snippets" in want:
            out["snippets"] = await self.snippet_repo.search(
                workspace_id=workspace_id, q=q, limit=limit_per_group)
        if "bookmarks" in want:
            out["bookmarks"] = await self.bookmark_repo.search(
                workspace_id=workspace_id, q=q, limit=limit_per_group)
        return out
