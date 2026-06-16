"""add generated tsvector columns + GIN indexes for full-text search

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-06-16

Phase 2.5: index-backed, rankable search on projects and tasks. The columns are
STORED generated columns so Postgres maintains them automatically on write; the
app never sets them. Snippets/bookmarks live in MongoDB with their own text
indexes, so they're unaffected.
"""
from alembic import op

revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE projects ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english',
                coalesce(name, '') || ' ' || coalesce(description, ''))
        ) STORED
        """
    )
    op.execute(
        "CREATE INDEX ix_projects_search_vector "
        "ON projects USING gin (search_vector)"
    )
    op.execute(
        """
        ALTER TABLE tasks ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english',
                coalesce(title, '') || ' ' || coalesce(description, ''))
        ) STORED
        """
    )
    op.execute(
        "CREATE INDEX ix_tasks_search_vector "
        "ON tasks USING gin (search_vector)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tasks_search_vector")
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS search_vector")
    op.execute("DROP INDEX IF EXISTS ix_projects_search_vector")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS search_vector")
