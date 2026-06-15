"""add outbox table

Revision ID: c4d5e6f7a8b9
Revises: 92d3db9d82b8
Create Date: 2026-06-16

outbox implements the transactional outbox pattern: domain events are written
to this table in the same DB transaction as the state change, then an arq
worker polls and dispatches them to handlers (activity, notifications, webhooks).
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "92d3db9d82b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("workspace_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_workspace_id", "outbox", ["workspace_id"])
    # Partial index — only unprocessed rows; keeps it tiny even with high volume.
    op.create_index(
        "ix_outbox_unprocessed",
        "outbox",
        ["created_at"],
        postgresql_where=sa.text("processed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_unprocessed", table_name="outbox")
    op.drop_index("ix_outbox_workspace_id", table_name="outbox")
    op.drop_table("outbox")
