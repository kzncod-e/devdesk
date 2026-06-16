"""Email delivery jobs — immediate per-notification sends and a daily digest cron."""
import logging
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.models.user import User
from app.repositories.notification_repo import NotificationRepository

logger = logging.getLogger(__name__)


def _format_notification(n_type: str, payload: dict) -> tuple[str, str]:
    actor = payload.get("actor_name", "Someone")
    if n_type == "task.assigned":
        title = payload.get("task_title") or "a task"
        return (
            f"Assigned to \"{title}\"",
            f"{actor} assigned you to \"{title}\".",
        )
    if n_type == "workspace.invite":
        ws = payload.get("workspace_name") or "a workspace"
        role = payload.get("role", "member")
        return (
            f"Invited to {ws}",
            f"{actor} invited you to join {ws} as {role}.",
        )
    if n_type == "member.role_changed":
        ws = payload.get("workspace_name") or "a workspace"
        new_role = payload.get("new_role", "member")
        return (
            f"Role updated in {ws}",
            f"Your role in {ws} was changed to {new_role}.",
        )
    return ("DevDesk notification", str(payload))


def _send_smtp(*, to: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host:
        logger.info("email (dev/stub) → %s | %s | %s", to, subject, body)
        return

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_user:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


async def send_notification_email(ctx: dict, notification_id: int) -> None:
    """Send a single notification email (enqueued by the outbox handler)."""
    maker: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    async with maker() as session:
        repo = NotificationRepository(session)
        row = await repo.get(notification_id)
        if row is None:
            return
        user = await session.get(User, row.user_id)
        if user is None:
            return
        subject, body = _format_notification(row.type, row.payload)
        app_url = get_settings().app_base_url
        if app_url:
            body += f"\n\nOpen DevDesk: {app_url}/app"
        _send_smtp(to=user.email, subject=f"[DevDesk] {subject}", body=body)


async def send_daily_digest(ctx: dict) -> None:
    """Cron: email each user a summary of unread notifications from the last 24 h."""
    maker: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    async with maker() as session:
        repo = NotificationRepository(session)
        rows = await repo.list_unread_for_digest(since=since)
        by_user: dict[int, list] = {}
        for row in rows:
            by_user.setdefault(row.user_id, []).append(row)

        for user_id, notes in by_user.items():
            user = await session.get(User, user_id)
            if user is None:
                continue
            lines = []
            for n in notes[:20]:
                subject, _ = _format_notification(n.type, n.payload)
                lines.append(f"• {subject}")
            extra = len(notes) - 20
            if extra > 0:
                lines.append(f"• …and {extra} more")
            body = "Here's what you missed in DevDesk:\n\n" + "\n".join(lines)
            app_url = get_settings().app_base_url
            if app_url:
                body += f"\n\nOpen DevDesk: {app_url}/app"
            _send_smtp(
                to=user.email,
                subject=f"[DevDesk] Daily digest ({len(notes)} unread)",
                body=body,
            )
