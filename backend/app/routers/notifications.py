from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_session
from app.repositories.notification_repo import NotificationRepository
from app.schemas.notification import (
    MarkReadIn,
    NotificationOut,
    NotificationPageOut,
    UnreadCountOut,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["notifications"])

CurrentUser = Annotated[object, Depends(get_current_user)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/notifications", response_model=NotificationPageOut)
async def list_notifications(
    user: CurrentUser,
    session: Session,
    before: int | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
):
    repo = NotificationRepository(session)
    rows = await repo.list_for_user(user.id, before_id=before, limit=limit)
    next_cursor = rows[-1]["id"] if len(rows) == limit else None
    return {"items": rows, "next_cursor": next_cursor}


@router.get("/notifications/unread-count", response_model=UnreadCountOut)
async def unread_count(user: CurrentUser, session: Session):
    count = await NotificationRepository(session).unread_count(user.id)
    return {"count": count}


@router.post("/notifications/read")
async def mark_read(body: MarkReadIn, user: CurrentUser, session: Session):
    updated = await NotificationRepository(session).mark_read(
        user.id, ids=body.ids, mark_all=body.all
    )
    await session.commit()
    return {"updated": updated}
