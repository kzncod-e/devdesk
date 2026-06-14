from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.repositories.snippet_repo import _to_api, parse_object_id


class BookmarkRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self.col = db.bookmarks

    async def create(self, *, workspace_id: int, owner_id: int, url: str,
                     tags: list[str], project_id: int | None) -> dict:
        doc = {
            "workspace_id": workspace_id,
            "owner_id": owner_id,
            "project_id": project_id,
            "url": url,
            "title": "",
            "description": "",
            "tags": tags,
            "favicon": "",
            "fetched_meta": {},
            "created_at": datetime.now(timezone.utc),
        }
        res = await self.col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return _to_api(doc)

    async def list(self, *, workspace_id: int, project_id: int | None = None,
                   tag: str | None = None, limit: int, offset: int) -> list[dict]:
        query: dict[str, Any] = {"workspace_id": workspace_id}
        if project_id is not None:
            query["project_id"] = project_id
        if tag is not None:
            query["tags"] = tag
        cursor = self.col.find(query).sort("created_at", -1).skip(offset).limit(limit)
        return [_to_api(doc) async for doc in cursor]

    async def get(self, bookmark_id: str, workspace_id: int) -> dict | None:
        oid = parse_object_id(bookmark_id)
        if oid is None:
            return None
        doc = await self.col.find_one({"_id": oid, "workspace_id": workspace_id})
        return _to_api(doc) if doc else None

    async def update(self, bookmark_id: str, workspace_id: int, *, fields: dict) -> dict | None:
        oid = parse_object_id(bookmark_id)
        if oid is None:
            return None
        doc = await self.col.find_one_and_update(
            {"_id": oid, "workspace_id": workspace_id},
            {"$set": fields},
            return_document=True,
        )
        return _to_api(doc) if doc else None

    async def set_metadata(self, bookmark_id: str, *, title: str, description: str,
                           favicon: str, fetched_meta: dict) -> dict | None:
        oid = parse_object_id(bookmark_id)
        if oid is None:
            return None
        doc = await self.col.find_one_and_update(
            {"_id": oid},
            {"$set": {"title": title, "description": description,
                      "favicon": favicon, "fetched_meta": fetched_meta}},
            return_document=True,
        )
        return _to_api(doc) if doc else None

    async def delete(self, bookmark_id: str, workspace_id: int) -> bool:
        oid = parse_object_id(bookmark_id)
        if oid is None:
            return False
        res = await self.col.delete_one({"_id": oid, "workspace_id": workspace_id})
        return res.deleted_count == 1

    async def search(self, *, workspace_id: int, q: str, limit: int) -> list[dict]:
        cursor = (
            self.col.find({"workspace_id": workspace_id, "$text": {"$search": q}})
            .sort([("score", {"$meta": "textScore"})])
            .limit(limit)
        )
        return [_to_api(doc) async for doc in cursor]

    async def detach_project(self, project_id: int) -> None:
        await self.col.update_many({"project_id": project_id},
                                   {"$set": {"project_id": None}})

    async def count_for_project(self, project_id: int) -> int:
        return await self.col.count_documents({"project_id": project_id})
