from pydantic import BaseModel, Field

Tags = Field(default_factory=list, max_length=20)


class SnippetIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    language: str = Field(min_length=1, max_length=50)
    code: str = Field(max_length=100_000)
    tags: list[str] = Tags
    notes: str = ""
    project_id: int | None = None


class SnippetPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    language: str | None = Field(default=None, min_length=1, max_length=50)
    code: str | None = Field(default=None, max_length=100_000)
    tags: list[str] | None = Field(default=None, max_length=20)
    notes: str | None = None
    project_id: int | None = None


class SnippetOut(BaseModel):
    id: int
    project_id: int | None
    title: str
    language: str
    code: str
    tags: list[str]
    notes: str
