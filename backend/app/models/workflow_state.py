from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class WorkflowState(Base):
    """A per-project board column. `category` maps the state to the coarse
    todo|in_progress|done bucket that `tasks.status` (and the summary) still use,
    so custom columns work without rewriting status-based reporting."""

    __tablename__ = "workflow_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(50))
    # todo | in_progress | done — keeps tasks.status a valid projection.
    category: Mapped[str] = mapped_column(String(20), default="todo")
    position: Mapped[float] = mapped_column(Float, default=1000.0)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_workflow_states_project", "project_id", "position"),
    )


# Seeded for every project; the order here is the initial column order.
DEFAULT_STATES = [
    {"name": "Todo", "category": "todo", "position": 1000.0, "color": "#71717a"},
    {"name": "In Progress", "category": "in_progress", "position": 2000.0, "color": "#e6a700"},
    {"name": "Done", "category": "done", "position": 3000.0, "color": "#30a46c"},
]
