"""arq worker — polls the outbox table every 5 s and dispatches domain events.

Start with:
    arq app.platform.worker.WorkerSettings

The worker is the only consumer of the outbox; it uses SELECT … FOR UPDATE SKIP
LOCKED so multiple replicas can run safely without double-processing.
"""
import logging
import os
from datetime import datetime, timezone

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.postgres import SessionLocal
from app.models.outbox import OutboxEvent
from app.platform.handlers import dispatch

logger = logging.getLogger(__name__)

POLL_BATCH = 50
MAX_ATTEMPTS = 5


async def poll_outbox(ctx: dict) -> None:
    """Fetch unprocessed outbox events and dispatch them to handlers."""
    maker: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    async with maker() as session:
        result = await session.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.processed_at.is_(None),
                OutboxEvent.attempts < MAX_ATTEMPTS,
            )
            .order_by(OutboxEvent.created_at)
            .limit(POLL_BATCH)
            .with_for_update(skip_locked=True)
        )
        events = list(result.scalars().all())

        for event in events:
            try:
                await dispatch(event.topic, event.payload)
                event.processed_at = datetime.now(timezone.utc)
            except Exception as exc:
                event.attempts += 1
                event.error = str(exc)
                logger.exception(
                    "outbox handler error — id=%s topic=%s attempt=%s",
                    event.id, event.topic, event.attempts,
                )

        if events:
            await session.commit()
            logger.debug("outbox: processed %d event(s)", len(events))


async def on_startup(ctx: dict) -> None:
    ctx["session_factory"] = SessionLocal


async def on_shutdown(ctx: dict) -> None:
    pass


class WorkerSettings:
    functions: list = []
    cron_jobs = [
        cron(poll_outbox, second={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings = RedisSettings.from_dsn(
        os.environ.get("REDIS_URL", "redis://localhost:6379")
    )
