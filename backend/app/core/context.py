"""Per-request context propagated via Python contextvars.

asyncio preserves ContextVar values across awaits within the same task, so
values set inside a FastAPI dependency are visible throughout the request.
"""
from contextvars import ContextVar

current_actor_id: ContextVar[int | None] = ContextVar("current_actor_id", default=None)
