from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificationEvent(models.TextChoices):
    """Events that notify users (thesis Table 9 plus implementation events)."""

    REQUEST_SUBMITTED = "request_submitted", "Request submitted"
    QUOTATION_SENT = "quotation_sent", "Quotation sent"
    QUOTATION_DECIDED = "quotation_decided", "Quotation decided"
    REVISION_UPLOADED = "revision_uploaded", "Design revision uploaded"
    REVISION_CHANGES_REQUESTED = "revision_changes_requested", "Changes requested on a revision"
    REVISION_APPROVED = "revision_approved", "Design approved"
    DECISION_REMINDER = "decision_reminder", "Decision reminder"
    DECISION_OVERDUE_ALERT = "decision_overdue_alert", "Decision overdue alert"
    STAGE_CHANGED = "stage_changed", "Stage changed"
    PROJECT_TURNED_OVER = "project_turned_over", "Project turned over"
    DESIGN_REOPENED = "design_reopened", "Design reopened"
    CHANGE_REQUESTED_BY_CLIENT = "change_requested_by_client", "Change requested by the client"


class EmailStatus(models.TextChoices):
    LOGGED = "logged", "Logged (not sent)"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"


class Notification(models.Model):
    """An in-app notification for one user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    event = models.CharField(max_length=40, choices=NotificationEvent.choices)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    # Path in the React app that the notification opens, for example /portal/projects/12/designs
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} → {self.user.email}"


class EmailLog(models.Model):
    """Every email FabriSee produced (the "Email outbox" of the administrator)."""

    to = models.CharField(max_length=320)
    subject = models.CharField(max_length=255)
    body_text = models.TextField()
    body_html = models.TextField(blank=True)
    status = models.CharField(
        max_length=10, choices=EmailStatus.choices, default=EmailStatus.LOGGED
    )
    error = models.TextField(blank=True)
    notification = models.ForeignKey(
        Notification, null=True, blank=True, on_delete=models.SET_NULL, related_name="emails"
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "email log entry"
        verbose_name_plural = "email log"

    def __str__(self):
        return f"{self.subject} → {self.to}"
