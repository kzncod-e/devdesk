from pydantic import BaseModel

from app.schemas.bookmark import BookmarkOut
from app.schemas.project import ProjectOut
from app.schemas.snippet import SnippetOut
from app.schemas.task import TaskOut


class SearchOut(BaseModel):
    projects: list[ProjectOut]
    tasks: list[TaskOut]
    snippets: list[SnippetOut]
    bookmarks: list[BookmarkOut]
