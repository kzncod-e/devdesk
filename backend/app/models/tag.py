from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Tag(Base):
    """Per-workspace tag registry: the canonical name→color mapping that powers
    autocomplete and colored chips. The source of truth for *what is tagged*
    remains the `text[]` arrays on snippets/bookmarks; this table is a catalog
    that self-populates as tags are used."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"), primary_key=True
    )
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_tags_workspace_name"),
    )
