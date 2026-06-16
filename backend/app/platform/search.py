"""Full-text search query builder.

Production (PostgreSQL) searches against generated `search_vector` tsvector
columns backed by GIN indexes (see migration f3a4b5c6d7e8), ranks hits with
`ts_rank`, and supports prefix matching so partial words ("proj") match while
the user is still typing. The SQLite API-test tier falls back to ILIKE.
"""
from __future__ import annotations

import re

from sqlalchemy import Float, column, func, or_
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

# Keep word characters; everything else becomes a term separator. Avoids
# feeding tsquery operators (& | ! : *) straight from user input.
_TERM_RE = re.compile(r"\w+", re.UNICODE)


def _prefix_tsquery(q: str):
    """Build a prefix tsquery: each term ANDed, last char allows prefix match.

    "data mod" -> to_tsquery('english', 'data:* & mod:*')
    """
    terms = _TERM_RE.findall(q.lower())
    if not terms:
        return None
    expr = " & ".join(f"{t}:*" for t in terms)
    return func.to_tsquery("english", expr)


def is_postgres(session: AsyncSession) -> bool:
    return session.bind.dialect.name == "postgresql"


def vector_match(session: AsyncSession, vector_name: str, *fallback_columns, q: str):
    """Boolean WHERE clause matching `q` against a generated tsvector column.

    On SQLite (no tsvector column exists) it ILIKEs the raw fallback columns.
    """
    if is_postgres(session):
        tsquery = _prefix_tsquery(q)
        if tsquery is None:
            return or_(*(col.ilike(f"%{q}%") for col in fallback_columns))
        return column(vector_name, TSVECTOR).op("@@")(tsquery)
    return or_(*(col.ilike(f"%{q}%") for col in fallback_columns))


def rank(session: AsyncSession, vector_name: str, *, q: str) -> ColumnElement[float]:
    """ts_rank ordering expression; constant on SQLite (no ranking there)."""
    if is_postgres(session):
        tsquery = _prefix_tsquery(q)
        if tsquery is not None:
            return func.ts_rank(column(vector_name, TSVECTOR), tsquery)
    return func.cast(0, Float)
