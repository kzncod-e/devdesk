from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    avatar_url: str | None = None


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: str = Field(default="medium", pattern=r"^(low|medium|high)$")
    due_date: date | None = None
    parent_task_id: int | None = None
    state_id: int | None = None
    assignee_ids: list[int] = Field(default_factory=list)


class AssigneesIn(BaseModel):
    user_ids: list[int] = Field(default_factory=list)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = Field(default=None, pattern=r"^(todo|in_progress|done)$")
    state_id: int | None = None
    priority: str | None = Field(default=None, pattern=r"^(low|medium|high)$")
    position: float | None = None
    due_date: date | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    workspace_id: int
    number: int | None = None
    parent_task_id: int | None = None
    state_id: int | None = None
    title: str
    description: str
    status: str
    priority: str
    position: float
    due_date: date | None
    assignees: list[UserBrief] = Field(default_factory=list)


class TaskCounts(BaseModel):
    todo: int
    in_progress: int
    done: int
    total: int


class ProjectSummaryOut(BaseModel):
    tasks: TaskCounts
    snippets: int
    bookmarks: int
