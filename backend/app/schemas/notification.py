from datetime import datetime

from pydantic import BaseModel, Field


class NotificationOut(BaseModel):
    id: int
    workspace_id: int
    type: str
    payload: dict
    read_at: datetime | None
    created_at: datetime


class NotificationPageOut(BaseModel):
    items: list[NotificationOut]
    next_cursor: int | None


class UnreadCountOut(BaseModel):
    count: int


class MarkReadIn(BaseModel):
    ids: list[int] = Field(default_factory=list)
    all: bool = False
