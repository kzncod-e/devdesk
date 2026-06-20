"""Outbox handlers for comments (Phase 3.1).

One `comment.created` event →
  • an activity row ("X commented on <task>"),
  • an audit row,
  • notifications to @mentioned users and to the task's assignees.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.models.task import Task
from app.platform.handlers import register
from app.platform.handlers.notifications import _actor_name, _notify


@register("comment.created")
async def on_comment_created(
    payload: dict, workspace_id: int | None, session: AsyncSession
) -> None:
    if workspace_id is None:
        return

    actor_id = payload.get("actor_id")
    entity_type = payload.get("entity_type") or "task"
    entity_id = payload.get("entity_id")
    task_title = payload.get("task_title", "")
    project_id = payload.get("project_id")
    excerpt = payload.get("excerpt", "")
    comment_id = payload.get("id")
    mention_ids = payload.get("mention_ids") or []

    actor = await _actor_name(session, actor_id)

    # Activity — user-facing "commented" entry, linked to the task it's on.
    session.add(Activity(
        workspace_id=workspace_id,
        actor_id=actor_id,
        verb="commented",
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=task_title,
        meta={"excerpt": excerpt, "comment_id": comment_id, "project_id": project_id},
    ))
    # Audit — compliance ledger.
    session.add(AuditLog(
        workspace_id=workspace_id,
        actor_id=actor_id,
        action="comment.created",
        target_type=entity_type,
        target_id=entity_id,
        after_state=payload,
    ))

    body = {
        "actor_id": actor_id,
        "actor_name": actor,
        "task_id": entity_id,
        "task_title": task_title,
        "project_id": project_id,
        "comment_id": comment_id,
        "excerpt": excerpt,
    }

    notified: set[int] = set()

    # @mentions — highest signal, worth an email.
    for uid in mention_ids:
        uid = int(uid)
        if uid == actor_id or uid in notified:
            continue
        await _notify(
            session, user_id=uid, workspace_id=workspace_id,
            type="comment.mention", payload=body,
        )
        notified.add(uid)

    # Task assignees — a new comment on a task they own (quieter, no email).
    if entity_type == "task" and entity_id:
        task = await session.get(Task, entity_id)
        if task is not None:
            for u in task.assignees:
                if u.id == actor_id or u.id in notified:
                    continue
                await _notify(
                    session, user_id=u.id, workspace_id=workspace_id,
                    type="comment.created", payload=body, email=False,
                )
                notified.add(u.id)
