from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Kind = Literal["project", "snippet"]
Visibility = Literal["workspace", "public"]


class CaptureIn(BaseModel):
    kind: Kind
    source_id: int
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    visibility: Visibility = "workspace"


class TemplateIn(BaseModel):
    """Create a template directly from a payload (no existing source)."""
    kind: Kind
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    payload: dict = Field(default_factory=dict)
    visibility: Visibility = "workspace"


class TemplateOut(BaseModel):
    id: int
    workspace_id: int | None
    kind: str
    name: str
    description: str
    visibility: str
    created_by: int | None
    use_count: int
    created_at: datetime


class TemplateDetailOut(TemplateOut):
    payload: dict


class UseResultOut(BaseModel):
    kind: str
    project_id: int | None = None
    snippet_id: int | None = None
