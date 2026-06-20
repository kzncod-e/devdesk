from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    color: str = Field(default="#71717a", pattern=r"^#[0-9a-fA-F]{6}$")
    image_url: str | None = Field(default=None, max_length=500)


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, pattern=r"^(active|archived)$")
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    image_url: str | None = Field(default=None, max_length=500)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    name: str
    key: str | None = None
    description: str
    status: str
    color: str
    image_url: str | None = None
    updated_at: datetime | None = None
    # Top-level task count; populated by the list endpoint (None elsewhere).
    task_count: int | None = None
