from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent


async def emit(
    session: AsyncSession,
    topic: str,
    payload: dict,
    *,
    workspace_id: int | None = None,
) -> None:
    """Add an outbox event to the current session unit-of-work.

    The caller must commit the session — the event is persisted atomically
    with the state change that triggered it (transactional outbox pattern).
    """
    session.add(OutboxEvent(topic=topic, payload=payload, workspace_id=workspace_id))
