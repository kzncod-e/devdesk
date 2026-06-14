from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres import Base
from app.models.user import User

# Many-to-many join: which users are assigned to a task.
task_assignees = Table(
    "task_assignees",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    # Denormalized from the parent project for cheap workspace-scoped queries.
    workspace_id: Mapped[int | None] = mapped_column(
        ForeignKey("workspaces.id"), index=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="todo")  # todo|in_progress|done
    priority: Mapped[str] = mapped_column(String(10), default="medium")  # low|medium|high
    position: Mapped[float] = mapped_column(Float)
    due_date: Mapped[date | None] = mapped_column(Date, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Eager-loaded in a single extra query when listing tasks (avoids N+1).
    assignees: Mapped[list[User]] = relationship(
        secondary=task_assignees, lazy="selectin", order_by=User.name
    )
