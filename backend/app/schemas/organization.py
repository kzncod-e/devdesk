"""Schemas for Phase 2.7 organization primitives: collections, tags, saved filters."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CollectionKind = Literal["snippet", "bookmark"]
FilterKind = Literal["snippet", "bookmark", "task", "project"]
_HEX = r"^#[0-9a-fA-F]{6}$"


# ── Collections ──────────────────────────────────────────────────────────────
class CollectionIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: CollectionKind
    parent_id: int | None = None


class CollectionPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    # Sentinel-free: presence of the key in the request drives the move (handled
    # in the router via model_fields_set).
    parent_id: int | None = None


class CollectionOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    kind: str
    parent_id: int | None


# ── Tags ─────────────────────────────────────────────────────────────────────
class TagColorPatch(BaseModel):
    color: str = Field(pattern=_HEX)


class TagOut(BaseModel):
    id: int
    name: str
    color: str


# ── Saved filters ──────────────────────────────────────────────────────────────
class SavedFilterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    kind: FilterKind
    query: dict = Field(default_factory=dict)


class SavedFilterOut(BaseModel):
    id: int
    name: str
    kind: str
    query: dict
    created_at: datetime
