# annotations deferred: methods named `list` would otherwise shadow the
# builtin when return annotations are evaluated in the class body
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.asynchronous.database import AsyncDatabase


def _to_api(doc: dict[str, Any]) -> dict[str, Any]:
    doc["id"] = str(doc.pop("_id"))
    return doc


def parse_object_id(value: str) -> ObjectId | None:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


class SnippetRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self.col = db.snippets

    async def create(self, *, owner_id: int, title: str, language: str, code: str,
                     tags: list[str], notes: str, project_id: int | None) -> dict:
        now = datetime.now(timezone.utc)
        doc = {
            "owner_id": owner_id,
            "project_id": project_id,
            "title": title,
            "language": language,
            "code": code,
            "tags": tags,
            "notes": notes,
            "created_at": now,
            "updated_at": now,
        }
        res = await self.col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return _to_api(doc)

    async def list(self, *, owner_id: int, project_id: int | None = None,
                   tag: str | None = None, language: str | None = None,
                   limit: int, offset: int) -> list[dict]:
        query: dict[str, Any] = {"owner_id": owner_id}
        if project_id is not None:
            query["project_id"] = project_id
        if tag is not None:
            query["tags"] = tag
        if language is not None:
            query["language"] = language
        cursor = self.col.find(query).sort("created_at", -1).skip(offset).limit(limit)
        return [_to_api(doc) async for doc in cursor]

    async def get(self, snippet_id: str, owner_id: int) -> dict | None:
        oid = parse_object_id(snippet_id)
        if oid is None:
            return None
        doc = await self.col.find_one({"_id": oid, "owner_id": owner_id})
        return _to_api(doc) if doc else None

    async def update(self, snippet_id: str, owner_id: int, *, fields: dict) -> dict | None:
        oid = parse_object_id(snippet_id)
        if oid is None:
            return None
        fields = {**fields, "updated_at": datetime.now(timezone.utc)}
        doc = await self.col.find_one_and_update(
            {"_id": oid, "owner_id": owner_id},
            {"$set": fields},
            return_document=True,
        )
        return _to_api(doc) if doc else None

    async def delete(self, snippet_id: str, owner_id: int) -> bool:
        oid = parse_object_id(snippet_id)
        if oid is None:
            return False
        res = await self.col.delete_one({"_id": oid, "owner_id": owner_id})
        return res.deleted_count == 1

    async def search(self, *, owner_id: int, q: str, limit: int) -> list[dict]:
        cursor = (
            self.col.find({"owner_id": owner_id, "$text": {"$search": q}})
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )
        return [_to_api(doc) async for doc in cursor]

    async def detach_project(self, project_id: int) -> None:
        await self.col.update_many({"project_id": project_id},
                                   {"$set": {"project_id": None}})

    async def count_for_project(self, project_id: int) -> int:
        return await self.col.count_documents({"project_id": project_id})
