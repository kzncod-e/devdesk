"""Domain event handler registry.

Usage:
    @register("project.created")
    async def on_project_created(payload: dict) -> None:
        ...

Phase 2.3 will register activity/audit handlers here.
Phase 2.4 will register notification handlers here.
"""
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

Handler = Callable[[dict], Awaitable[None]]

_registry: dict[str, list[Handler]] = {}


def register(topic: str) -> Callable[[Handler], Handler]:
    def decorator(fn: Handler) -> Handler:
        _registry.setdefault(topic, []).append(fn)
        return fn
    return decorator


async def dispatch(topic: str, payload: dict) -> None:
    handlers = _registry.get(topic, [])
    if not handlers:
        logger.debug("outbox: unhandled topic %s payload=%s", topic, payload)
        return
    for handler in handlers:
        await handler(payload)
