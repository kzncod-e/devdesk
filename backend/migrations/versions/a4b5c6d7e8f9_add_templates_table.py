"""add templates table

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-06-18

Phase 2.6: reusable project/snippet templates. workspace_id NULL = global;
visibility 'public' surfaces the row in the unauthenticated gallery.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "a4b5c6d7e8f9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "templates",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("payload", JSONB(), nullable=False, server_default="{}"),
        sa.Column("visibility", sa.String(20), nullable=False,
                  server_default="workspace"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("use_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_templates_workspace_id", "templates", ["workspace_id"])
    op.create_index("ix_templates_workspace_kind", "templates", ["workspace_id", "kind"])
    op.create_index("ix_templates_gallery", "templates", ["visibility", "kind"])


def downgrade() -> None:
    op.drop_index("ix_templates_gallery", table_name="templates")
    op.drop_index("ix_templates_workspace_kind", table_name="templates")
    op.drop_index("ix_templates_workspace_id", table_name="templates")
    op.drop_table("templates")
