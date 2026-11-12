"""In-app notifications and email.

`notify()` is the single entry point: every service that changes something calls it.
This is the Milestone 1 version: it writes `Notification` rows and logs one plain-text
email per recipient. Milestone 7 adds the HTML templates and groups bursts of the same
event into one notification.
"""

import logging
from collections.abc import Iterable
from datetime import datetime

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from apps.core.models import SystemSetting
from apps.projects.links import project_path

from .backends import EMAIL_LOG_HEADER
from .models import EmailLog, EmailStatus, Notification

logger = logging.getLogger(__name__)

DATABASE_BACKEND = "apps.notifications.backends.DatabaseEmailBackend"


def email_subject(title: str, project=None) -> str:
    """`[FabriSee] FS-2026-0007 · Design R2 is waiting for your approval`."""
    if project is not None:
        return f"[FabriSee] {project.project_number} · {title}"
    return f"[FabriSee] {title}"


def render_email_text(*, user, title: str, message: str, link: str, project=None) -> str:
    """The plain-text body of a notification email."""
    company = SystemSetting.load().company_name
    lines = [f"Hello {user.full_name},", "", title]
    if message:
        lines += ["", message]
    if project is not None:
        lines += ["", f"Project: {project.project_number} · {project.title}"]
    if link:
        lines += ["", f"Open in FabriSee: {settings.FRONTEND_URL}{link}"]
    lines += ["", "--", f"FabriSee · {company}", "This is an automated message."]
    return "\n".join(lines)


def deliver_email(email_log_id: int) -> None:
    """Hand a logged email to the configured email backend and record the outcome."""
    log = EmailLog.objects.filter(pk=email_log_id).first()
    if log is None:
        return
    message = EmailMultiAlternatives(
        subject=log.subject,
        body=log.body_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[log.to],
        headers={EMAIL_LOG_HEADER: str(log.pk)},
    )
    if log.body_html:
        message.attach_alternative(log.body_html, "text/html")
    try:
        message.send(fail_silently=False)
    except Exception as exc:  # the mail server may be down; the log keeps the message
        logger.warning("Email to %s could not be sent: %s", log.to, exc)
        EmailLog.objects.filter(pk=log.pk).update(status=EmailStatus.FAILED, error=str(exc)[:2000])
        return
    if settings.EMAIL_BACKEND != DATABASE_BACKEND:
        EmailLog.objects.filter(pk=log.pk).update(status=EmailStatus.SENT, error="")


def queue_email(
    *, to: str, subject: str, body_text: str, body_html: str = "", notification=None
) -> EmailLog:
    """Write the email to the log now; send it once the current transaction commits."""
    log = EmailLog.objects.create(
        to=to,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        notification=notification,
        status=EmailStatus.LOGGED,
    )
    transaction.on_commit(lambda: deliver_email(log.pk))
    return log


def notify(
    *,
    event: str,
    recipients: Iterable,
    title: str,
    message: str = "",
    project=None,
    section: str = "overview",
    actor=None,
    at: datetime | None = None,
) -> list[Notification]:
    """Notify users in the app and by email.

    * `recipients` may contain duplicates and `None`; each active user is notified once.
    * The person who caused the event (`actor`) is never notified.
    * `section` chooses the tab of the project page the notification opens
      (`overview`, `quotation`, `design`, `progress`, `documents`).
    """
    created: list[Notification] = []
    seen: set[int] = set()
    for user in recipients:
        if user is None or user.pk in seen:
            continue
        seen.add(user.pk)
        if not user.is_active or (actor is not None and user.pk == actor.pk):
            continue
        link = project_path(user, project, section) if project is not None else ""
        notification = Notification.objects.create(
            user=user,
            project=project,
            event=event,
            title=title,
            message=message,
            link=link,
            created_at=at or timezone.now(),
        )
        queue_email(
            to=user.email,
            subject=email_subject(title, project),
            body_text=render_email_text(
                user=user, title=title, message=message, link=link, project=project
            ),
            notification=notification,
        )
        created.append(notification)
    return created
