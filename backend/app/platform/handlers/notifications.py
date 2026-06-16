"""Outbox handlers that fan out domain events into per-user notifications."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.platform.handlers import register
from app.platform.jobs.enqueue import enqueue_job
from app.repositories.notification_repo import NotificationRepository


async def _actor_name(session: AsyncSession, actor_id: int | None) -> str:
    if actor_id is None:
        return "Someone"
    user = await session.get(User, actor_id)
    return user.name if user else "Someone"


async def _notify(
    session: AsyncSession,
    *,
    user_id: int,
    workspace_id: int,
    type: str,
    payload: dict,
    email: bool = True,
) -> None:
    if user_id == payload.get("actor_id"):
        return
    repo = NotificationRepository(session)
    row = await repo.create(
        user_id=user_id,
        workspace_id=workspace_id,
        type=type,
        payload=payload,
    )
    if email:
        await enqueue_job("send_notification_email", row.id)


@register("task.created")
async def on_task_created(
    payload: dict, workspace_id: int | None, session: AsyncSession
) -> None:
    if workspace_id is None:
        return
    actor_id = payload.get("actor_id")
    assignee_ids = payload.get("assignee_ids") or []
    actor = await _actor_name(session, actor_id)
    body = {
        "actor_id": actor_id,
        "actor_name": actor,
        "task_id": payload.get("id"),
        "task_title": payload.get("title", ""),
        "project_id": payload.get("project_id"),
    }
    for uid in assignee_ids:
        if uid == actor_id:
            continue
        await _notify(
            session,
            user_id=int(uid),
            workspace_id=workspace_id,
            type="task.assigned",
            payload=body,
        )


@register("task.assignees_changed")
async def on_task_assignees_changed(
    payload: dict, workspace_id: int | None, session: AsyncSession
) -> None:
    if workspace_id is None:
        return
    actor_id = payload.get("actor_id")
    added = payload.get("added_user_ids") or []
    if not added:
        return

    task_id = payload.get("id")
    task_title = payload.get("title", "")
    project_id = payload.get("project_id")
    if not task_title and task_id:
        task = await session.get(Task, task_id)
        if task:
            task_title = task.title
            project_id = project_id or task.project_id

    actor = await _actor_name(session, actor_id)
    body = {
        "actor_id": actor_id,
        "actor_name": actor,
        "task_id": task_id,
        "task_title": task_title,
        "project_id": project_id,
    }
    for uid in added:
        await _notify(
            session,
            user_id=int(uid),
            workspace_id=workspace_id,
            type="task.assigned",
            payload=body,
        )


@register("member.invited")
async def on_member_invited(
    payload: dict, workspace_id: int | None, session: AsyncSession
) -> None:
    if workspace_id is None:
        return
    email = payload.get("email", "")
    res = await session.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if user is None:
        return

    ws = await session.get(Workspace, workspace_id)
    actor = await _actor_name(session, payload.get("actor_id"))
    await _notify(
        session,
        user_id=user.id,
        workspace_id=workspace_id,
        type="workspace.invite",
        payload={
            "actor_id": payload.get("actor_id"),
            "actor_name": actor,
            "workspace_id": workspace_id,
            "workspace_name": ws.name if ws else "",
            "role": payload.get("role", "member"),
        },
    )


@register("member.role_changed")
async def on_member_role_changed(
    payload: dict, workspace_id: int | None, session: AsyncSession
) -> None:
    if workspace_id is None:
        return
    target_id = payload.get("user_id")
    actor_id = payload.get("actor_id")
    if target_id is None or target_id == actor_id:
        return

    ws = await session.get(Workspace, workspace_id)
    actor = await _actor_name(session, actor_id)
    await _notify(
        session,
        user_id=int(target_id),
        workspace_id=workspace_id,
        type="member.role_changed",
        payload={
            "actor_id": actor_id,
            "actor_name": actor,
            "workspace_id": workspace_id,
            "workspace_name": ws.name if ws else "",
            "old_role": payload.get("old_role"),
            "new_role": payload.get("new_role"),
        },
        email=False,
    )
