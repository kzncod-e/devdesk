from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError, UnprocessableError
from app.core.events import emit
from app.models.comment import Comment
from app.repositories.comment_repo import CommentRepository
from app.repositories.task_repo import TaskRepository
from app.repositories.workspace_repo import MembershipRepository


class CommentService:
    """Comments on workspace entities (tasks today).

    Membership + permission are enforced at the router via `require(perm)`; the
    service additionally pins every comment to an entity that actually lives in
    the caller's workspace, so a valid member of workspace A can't comment on
    workspace B's task by guessing an id.
    """

    def __init__(
        self,
        session: AsyncSession,
        comment_repo: CommentRepository,
        task_repo: TaskRepository,
        membership_repo: MembershipRepository,
    ) -> None:
        self.session = session
        self.comments = comment_repo
        self.tasks = task_repo
        self.members = membership_repo

    async def _resolve_entity(self, entity_type: str, entity_id: int, workspace_id: int):
        """Return (title, project_id) for the target entity, or raise if it isn't
        in this workspace. Only tasks are wired today."""
        if entity_type == "task":
            task = await self.tasks.get_in_workspace(entity_id, workspace_id)
            if task is None:
                raise NotFoundError("Task not found")
            return task.title, task.project_id
        raise UnprocessableError(f"Unsupported comment target: {entity_type}")

    async def list(self, *, entity_type: str, entity_id: int, workspace_id: int) -> list[Comment]:
        await self._resolve_entity(entity_type, entity_id, workspace_id)
        return await self.comments.list_for_entity(entity_type, entity_id)

    async def _valid_mentions(self, workspace_id: int, mention_ids: list[int]) -> list[int]:
        """Keep only ids that are active members of this workspace."""
        out: list[int] = []
        for uid in dict.fromkeys(mention_ids):  # de-dupe, preserve order
            m = await self.members.get(workspace_id, uid)
            if m is not None and m.status == "active":
                out.append(uid)
        return out

    async def create(
        self,
        *,
        workspace_id: int,
        author_id: int,
        entity_type: str,
        entity_id: int,
        body: str,
        parent_id: int | None = None,
        mention_ids: list[int] | None = None,
    ) -> Comment:
        title, project_id = await self._resolve_entity(entity_type, entity_id, workspace_id)

        if parent_id is not None:
            parent = await self.comments.get(parent_id)
            if (
                parent is None
                or parent.deleted_at is not None
                or parent.entity_type != entity_type
                or parent.entity_id != entity_id
            ):
                raise UnprocessableError("Invalid parent comment")

        mentions = await self._valid_mentions(workspace_id, mention_ids or [])

        comment = await self.comments.create(
            workspace_id=workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            body=body,
            parent_id=parent_id,
        )
        await emit(
            self.session,
            "comment.created",
            {
                "id": comment.id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "task_title": title,
                "project_id": project_id,
                "mention_ids": mentions,
                "excerpt": body[:140],
                "parent_id": parent_id,
            },
            workspace_id=workspace_id,
        )
        await self.session.commit()
        return comment

    async def update(self, comment_id: int, *, workspace_id: int, user_id: int, body: str) -> Comment:
        comment = await self._require_own(comment_id, workspace_id, user_id)
        updated = await self.comments.update_body(comment, body)
        await self.session.commit()
        return updated

    async def delete(
        self, comment_id: int, *, workspace_id: int, user_id: int, can_moderate: bool
    ) -> None:
        comment = await self._require_in_workspace(comment_id, workspace_id)
        if comment.author_id != user_id and not can_moderate:
            raise ForbiddenError("You can only delete your own comments")
        await self.comments.soft_delete(comment)
        await self.session.commit()

    async def _require_in_workspace(self, comment_id: int, workspace_id: int) -> Comment:
        comment = await self.comments.get(comment_id)
        if comment is None or comment.deleted_at is not None or comment.workspace_id != workspace_id:
            raise NotFoundError("Comment not found")
        return comment

    async def _require_own(self, comment_id: int, workspace_id: int, user_id: int) -> Comment:
        comment = await self._require_in_workspace(comment_id, workspace_id)
        if comment.author_id != user_id:
            raise ForbiddenError("You can only edit your own comments")
        return comment
