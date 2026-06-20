from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base

if TYPE_CHECKING:
    from app.models.user import User


class Comment(Base):
    """A threaded comment on a workspace entity (tasks today; generic by design).

    `entity_type` + `entity_id` is a polymorphic pointer (matches the roadmap's
    comments shape); `parent_id` gives one level of threading. Soft-deleted via
    `deleted_at` so threads keep their shape.
    """

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"), primary_key=True
    )
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Eager (selectin) so CommentOut.author maps without async lazy-load surprises.
    author: Mapped["User | None"] = relationship("User", lazy="selectin")

    __table_args__ = (
        # Primary read path: all comments for one entity, in order.
        Index("ix_comments_entity", "entity_type", "entity_id", "id"),
        Index("ix_comments_workspace_id", "workspace_id"),
    )
