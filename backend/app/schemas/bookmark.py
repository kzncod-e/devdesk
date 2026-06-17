from pydantic import BaseModel, Field, HttpUrl


class BookmarkIn(BaseModel):
    url: HttpUrl
    tags: list[str] = Field(default_factory=list, max_length=20)
    project_id: int | None = None
    collection_id: int | None = None


class BookmarkPatch(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = Field(default=None, max_length=20)
    project_id: int | None = None
    collection_id: int | None = None


class BookmarkOut(BaseModel):
    id: int
    project_id: int | None
    collection_id: int | None = None
    url: str
    title: str
    description: str
    tags: list[str]
    favicon: str
    fetched_meta: dict
