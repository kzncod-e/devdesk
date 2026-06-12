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
