from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base

# JSONB on Postgres; plain JSON on the SQLite test tier.
_PAYLOAD = JSONB().with_variant(JSON(), "sqlite")


class Template(Base):
    """A reusable, serialized project or snippet.

    `workspace_id` NULL = a global/system template available to every workspace.
    `visibility` 'public' surfaces the template in the unauthenticated gallery.
    `payload` is the serialized content (see services/template_service for shapes).
    """

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"), primary_key=True
    )
    workspace_id: Mapped[int | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # project|snippet
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(_PAYLOAD, default=dict)
    visibility: Mapped[str] = mapped_column(
        String(20), nullable=False, default="workspace"  # workspace|public
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_templates_workspace_kind", "workspace_id", "kind"),
        # Gallery: public templates ordered by popularity.
        Index("ix_templates_gallery", "visibility", "kind"),
    )
