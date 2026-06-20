from pydantic import BaseModel, ConfigDict, Field

_CATEGORY = r"^(todo|in_progress|done)$"


class WorkflowStateIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    category: str = Field(default="todo", pattern=_CATEGORY)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class WorkflowStatePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    category: str | None = Field(default=None, pattern=_CATEGORY)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    position: float | None = None


class WorkflowStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    category: str
    position: float
    color: str | None = None
