from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.task import UserBrief


class CommentIn(BaseModel):
    entity_type: str = Field(pattern=r"^(task)$")  # tasks today; widen as surfaces land
    entity_id: int
    body: str = Field(min_length=1, max_length=10_000)
    parent_id: int | None = None
    # User ids the author @mentioned (resolved by the composer's autocomplete);
    # validated against active workspace members server-side.
    mention_ids: list[int] = Field(default_factory=list)


class CommentPatch(BaseModel):
    body: str = Field(min_length=1, max_length=10_000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    author: UserBrief | None
    body: str
    parent_id: int | None
    created_at: datetime
    edited_at: datetime | None
