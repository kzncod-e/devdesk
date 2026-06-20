"""add workflow states + tasks.state_id

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-06-20

Phase 3.3 (part 2): custom per-project board columns. Seeds 3 default states per
project (Todo/In Progress/Done) and backfills tasks.state_id from tasks.status.
`status` is retained as a denormalized projection of the state's category.
"""
from alembic import op
import sqlalchemy as sa

revision = "e8f9a0b1c2d3"
down_revision = "d7e8f9a0b1c2"
branch_labels = None
depends_on = None

_DEFAULTS = [
    ("Todo", "todo", 1000.0, "#71717a"),
    ("In Progress", "in_progress", 2000.0, "#e6a700"),
    ("Done", "done", 3000.0, "#30a46c"),
]


def upgrade() -> None:
    op.create_table(
        "workflow_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("category", sa.String(20), nullable=False, server_default="todo"),
        sa.Column("position", sa.Float(), nullable=False, server_default="1000"),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_states_project", "workflow_states", ["project_id", "position"])

    op.add_column("tasks", sa.Column("state_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_state_id", "tasks", "workflow_states",
        ["state_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_tasks_state_id", "tasks", ["state_id"])

    bind = op.get_bind()
    projects = bind.execute(sa.text("SELECT id FROM projects")).fetchall()
    for (pid,) in projects:
        for name, cat, pos, color in _DEFAULTS:
            sid = bind.execute(
                sa.text(
                    "INSERT INTO workflow_states (project_id, name, category, position, color) "
                    "VALUES (:pid, :n, :c, :p, :col) RETURNING id"
                ),
                {"pid": pid, "n": name, "c": cat, "p": pos, "col": color},
            ).scalar()
            bind.execute(
                sa.text("UPDATE tasks SET state_id = :sid WHERE project_id = :pid AND status = :c"),
                {"sid": sid, "pid": pid, "c": cat},
            )


def downgrade() -> None:
    op.drop_index("ix_tasks_state_id", table_name="tasks")
    op.drop_constraint("fk_tasks_state_id", "tasks", type_="foreignkey")
    op.drop_column("tasks", "state_id")
    op.drop_index("ix_workflow_states_project", table_name="workflow_states")
    op.drop_table("workflow_states")
