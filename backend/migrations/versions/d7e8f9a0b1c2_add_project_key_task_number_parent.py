"""add project key + task number + parent_task_id

Revision ID: d7e8f9a0b1c2
Revises: c6d7e8f9a0b1
Create Date: 2026-06-20

Phase 3.3 (part 1): per-project task numbering (KEY-N identifiers) + sub-tasks.
Backfills project.key from the name and tasks.number per project (ordered by id).
"""
import re

from alembic import op
import sqlalchemy as sa

revision = "d7e8f9a0b1c2"
down_revision = "c6d7e8f9a0b1"
branch_labels = None
depends_on = None


def _key(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name or "")
    if not words:
        return "PRJ"
    if len(words) == 1:
        return words[0][:4].upper()
    return "".join(w[0] for w in words[:4]).upper()


def upgrade() -> None:
    op.add_column("projects", sa.Column("key", sa.String(10), nullable=True))
    op.add_column("tasks", sa.Column("number", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("parent_task_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_parent_task_id", "tasks", "tasks",
        ["parent_task_id"], ["id"], ondelete="CASCADE",
    )
    op.create_index("ix_tasks_parent_task_id", "tasks", ["parent_task_id"])

    bind = op.get_bind()
    projects = bind.execute(sa.text("SELECT id, name FROM projects")).fetchall()
    for pid, name in projects:
        bind.execute(
            sa.text("UPDATE projects SET key = :k WHERE id = :id"),
            {"k": _key(name), "id": pid},
        )
    for pid, _name in projects:
        rows = bind.execute(
            sa.text("SELECT id FROM tasks WHERE project_id = :pid ORDER BY id"),
            {"pid": pid},
        ).fetchall()
        for i, (tid,) in enumerate(rows, start=1):
            bind.execute(
                sa.text("UPDATE tasks SET number = :n WHERE id = :id"),
                {"n": i, "id": tid},
            )


def downgrade() -> None:
    op.drop_index("ix_tasks_parent_task_id", table_name="tasks")
    op.drop_constraint("fk_tasks_parent_task_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "parent_task_id")
    op.drop_column("tasks", "number")
    op.drop_column("projects", "key")
