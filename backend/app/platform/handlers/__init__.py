"""Domain event handler registry.

Usage:
    @register("project.created")
    async def on_project_created(
        payload: dict, workspace_id: int | None, session: AsyncSession
    ) -> None:
        ...

Phase 2.3 activity/audit handlers are in app/platform/handlers/activity.py.
Phase 2.4 notification handlers are in app/platform/handlers/notifications.py.
"""
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

Handler = Callable[[dict, int | None, AsyncSession], Awaitable[None]]

_registry: dict[str, list[Handler]] = {}


def register(topic: str) -> Callable[[Handler], Handler]:
    def decorator(fn: Handler) -> Handler:
        _registry.setdefault(topic, []).append(fn)
        return fn
    return decorator


async def dispatch(
    topic: str,
    payload: dict,
    *,
    workspace_id: int | None,
    session: AsyncSession,
) -> None:
    handlers = _registry.get(topic, [])
    if not handlers:
        logger.debug("outbox: unhandled topic %s payload=%s", topic, payload)
        return
    for handler in handlers:
        await handler(payload, workspace_id, session)
