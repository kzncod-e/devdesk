from collections.abc import AsyncIterator

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import get_settings

_client: AsyncMongoClient | None = None


def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        _client = AsyncMongoClient(get_settings().mongo_url)
    return _client


async def get_mongo_db() -> AsyncIterator[AsyncDatabase]:
    yield get_client()[get_settings().mongo_db_name]


async def ensure_mongo_indexes(db: AsyncDatabase) -> None:
    """Idempotent text indexes backing /search ($text requires them)."""
    # language_override points at an unused field: snippets carry a `language`
    # field (programming language) that Mongo would otherwise interpret as a
    # text-search language override and reject (e.g. "nginx")
    await db.snippets.create_index(
        [("title", "text"), ("code", "text"), ("notes", "text"), ("tags", "text")],
        name="snippets_text",
        language_override="text_lang",
    )
    await db.bookmarks.create_index(
        [("title", "text"), ("description", "text"), ("url", "text"), ("tags", "text")],
        name="bookmarks_text",
        language_override="text_lang",
    )
