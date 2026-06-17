"""add collections, tags, saved_filters + collection_id columns

Revision ID: b5c6d7e8f9a0
Revises: a4b5c6d7e8f9
Create Date: 2026-06-18

Phase 2.7: organization primitives.
- collections: self-referential folder tree, pinned to one entity kind.
- tags: per-workspace name→color registry (catalog over the existing text[] arrays).
- saved_filters: per-user named query blobs.
- snippets/bookmarks gain a nullable collection_id (SET NULL on folder delete).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "b5c6d7e8f9a0"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "collections",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["collections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_collections_workspace_id", "collections", ["workspace_id"])
    op.create_index("ix_collections_workspace_kind", "collections",
                    ["workspace_id", "kind"])

    op.create_table(
        "tags",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#6366f1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "name", name="uq_tags_workspace_name"),
    )
    op.create_index("ix_tags_workspace_id", "tags", ["workspace_id"])

    op.create_table(
        "saved_filters",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("query", JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_filters_user_ws_kind", "saved_filters",
                    ["user_id", "workspace_id", "kind"])

    op.add_column("snippets", sa.Column("collection_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key("fk_snippets_collection", "snippets", "collections",
                          ["collection_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_snippets_collection_id", "snippets", ["collection_id"])

    op.add_column("bookmarks", sa.Column("collection_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key("fk_bookmarks_collection", "bookmarks", "collections",
                          ["collection_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_bookmarks_collection_id", "bookmarks", ["collection_id"])


def downgrade() -> None:
    op.drop_index("ix_bookmarks_collection_id", table_name="bookmarks")
    op.drop_constraint("fk_bookmarks_collection", "bookmarks", type_="foreignkey")
    op.drop_column("bookmarks", "collection_id")
    op.drop_index("ix_snippets_collection_id", table_name="snippets")
    op.drop_constraint("fk_snippets_collection", "snippets", type_="foreignkey")
    op.drop_column("snippets", "collection_id")

    op.drop_index("ix_saved_filters_user_ws_kind", table_name="saved_filters")
    op.drop_table("saved_filters")
    op.drop_index("ix_tags_workspace_id", table_name="tags")
    op.drop_table("tags")
    op.drop_index("ix_collections_workspace_kind", table_name="collections")
    op.drop_index("ix_collections_workspace_id", table_name="collections")
    op.drop_table("collections")
