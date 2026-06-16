"""Enqueue arq background jobs from outbox handlers (runs inside the worker)."""
import logging
import os

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

logger = logging.getLogger(__name__)

_pool: ArqRedis | None = None


async def _get_redis() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(
            RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379"))
        )
    return _pool


async def enqueue_job(function_name: str, *args, **kwargs) -> None:
    try:
        redis = await _get_redis()
        await redis.enqueue_job(function_name, *args, **kwargs)
    except Exception:
        logger.exception("failed to enqueue arq job %s", function_name)
