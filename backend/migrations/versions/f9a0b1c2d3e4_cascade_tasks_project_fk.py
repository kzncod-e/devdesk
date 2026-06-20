"""cascade delete tasks when their project is deleted

Revision ID: f9a0b1c2d3e4
Revises: e8f9a0b1c2d3
Create Date: 2026-06-21

Deleting a project failed with a FK violation because tasks.project_id had no
ON DELETE action. Recreate the constraint with ON DELETE CASCADE so a project
delete cleans up its tasks (task_assignees + sub-tasks already cascade from tasks;
workflow_states cascade from the project).
"""
from alembic import op

revision = "f9a0b1c2d3e4"
down_revision = "e8f9a0b1c2d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("tasks_project_id_fkey", "tasks", type_="foreignkey")
    op.create_foreign_key(
        "tasks_project_id_fkey", "tasks", "projects",
        ["project_id"], ["id"], ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("tasks_project_id_fkey", "tasks", type_="foreignkey")
    op.create_foreign_key(
        "tasks_project_id_fkey", "tasks", "projects", ["project_id"], ["id"],
    )
