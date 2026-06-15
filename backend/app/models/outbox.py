from datetime import datetime, timezone

from sqlalchemy import BigInteger, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class OutboxEvent(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    workspace_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "ix_outbox_unprocessed",
            "created_at",
            postgresql_where="processed_at IS NULL",
        ),
    )
