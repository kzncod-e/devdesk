import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import current_actor_id
from app.models.outbox import OutboxEvent


def _json_default(o: object) -> object:
    """Coerce values the JSON column can't serialize into JSON-native ones.

    Event payloads frequently carry ORM field values like ``date``/``datetime``
    (e.g. a task's ``due_date``) which the default JSON serializer rejects.
    """
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, Decimal):
        return float(o)
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


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

    The payload is normalised to JSON-native types so values such as
    ``date``/``datetime`` are stored as ISO strings rather than raising on insert.
    """
    actor_id = current_actor_id.get()
    full_payload = {"actor_id": actor_id, **payload}
    clean_payload = json.loads(json.dumps(full_payload, default=_json_default))
    session.add(OutboxEvent(topic=topic, payload=clean_payload, workspace_id=workspace_id))
