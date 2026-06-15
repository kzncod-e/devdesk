from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import current_actor_id
from app.models.outbox import OutboxEvent


async def emit(
    session: AsyncSession,
    topic: str,
    payload: dict,
    *,
    workspace_id: int | None = None,
) -> None:
    """Add an outbox event to the current session unit-of-work.

    actor_id is automatically sourced from the request-scoped ContextVar set
    by get_current_user so every event payload includes who triggered it.
    The caller must commit — the event is persisted atomically with the state
    change (transactional outbox pattern).
    """
    actor_id = current_actor_id.get()
    full_payload = {"actor_id": actor_id, **payload}
    session.add(OutboxEvent(topic=topic, payload=full_payload, workspace_id=workspace_id))
