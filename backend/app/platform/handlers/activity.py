"""Outbox handlers that write to activities and audit_logs.

One emit() call → one outbox event → both ledgers updated here in the worker.
Import this module in app/main.py (or the worker startup) to register handlers.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.audit_log import AuditLog
from app.platform.handlers import register

# topic → (verb, entity_type, name_key_in_payload)
_TOPIC_MAP: dict[str, tuple[str, str, str | None]] = {
    "project.created":          ("created",          "project",   "name"),
    "project.updated":          ("updated",           "project",   None),
    "project.deleted":          ("deleted",           "project",   None),
    "task.created":             ("created",           "task",      "title"),
    "task.updated":             ("updated",           "task",      None),
    "task.status_changed":      ("status_changed",    "task",      None),
    "task.deleted":             ("deleted",           "task",      None),
    "task.assignees_changed":   ("assignees_changed", "task",      None),
    "snippet.created":          ("created",           "snippet",   "title"),
    "snippet.updated":          ("updated",           "snippet",   None),
    "snippet.deleted":          ("deleted",           "snippet",   None),
    "bookmark.created":         ("created",           "bookmark",  "url"),
    "member.invited":           ("invited",           "member",    "email"),
    "member.joined":            ("joined",            "member",    None),
    "member.role_changed":      ("role_changed",      "member",    None),
    "member.removed":           ("removed",           "member",    None),
    "workspace.created":        ("created",           "workspace", "name"),
}

# For member events, entity_id lives under a different key.
_ENTITY_ID_KEY: dict[str, str] = {
    "member": "user_id",
}


def _entity_id(payload: dict, entity_type: str) -> int | None:
    key = _ENTITY_ID_KEY.get(entity_type, "id")
    v = payload.get(key)
    return int(v) if v is not None else None


async def _handle_all(
    topic: str,
    payload: dict,
    workspace_id: int | None,
    session: AsyncSession,
) -> None:
    if workspace_id is None:
        return

    mapping = _TOPIC_MAP.get(topic)
    if mapping is None:
        return

    verb, entity_type, name_key = mapping
    actor_id = payload.get("actor_id")
    entity_id = _entity_id(payload, entity_type)
    entity_name = str(payload.get(name_key, "")) if name_key else ""

    # Activity — user-facing feed
    session.add(Activity(
        workspace_id=workspace_id,
        actor_id=actor_id,
        verb=verb,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        meta={k: v for k, v in payload.items() if k not in ("actor_id",)},
    ))

    # Audit log — compliance ledger
    session.add(AuditLog(
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=topic,
        target_type=entity_type,
        target_id=entity_id,
        after_state=payload,
    ))


def _make_handler(topic: str):
    async def handler(payload: dict, workspace_id: int | None, session: AsyncSession) -> None:
        await _handle_all(topic, payload, workspace_id, session)
    handler.__name__ = f"on_{topic.replace('.', '_')}"
    return handler


for _topic in _TOPIC_MAP:
    register(_topic)(_make_handler(_topic))
