from django.conf import settings
from django.db import models
from django.utils import timezone


class ActivityAction(models.TextChoices):
    """What happened. The counts per action feed the Chapter 4 export (guide 15.3)."""

    REQUEST_SUBMITTED = "request_submitted", "Request submitted"
    PROJECT_CREATED = "project_created", "Project created"
    PROJECT_UPDATED = "project_updated", "Project updated"
    APPROVERS_CHANGED = "approvers_changed", "Designated approvers changed"
    QUOTATION_CREATED = "quotation_created", "Quotation created"
    QUOTATION_SENT = "quotation_sent", "Quotation sent"
    QUOTATION_ACCEPTED = "quotation_accepted", "Quotation accepted"
    QUOTATION_RETURNED = "quotation_returned", "Quotation returned"
    REVISION_UPLOADED = "revision_uploaded", "Design revision uploaded"
    REVISION_SUPERSEDED = "revision_superseded", "Design revision superseded"
    REVISION_APPROVED_BY = "revision_approved_by", "Design revision approved by an approver"
    REVISION_CHANGES_REQUESTED_BY = (
        "revision_changes_requested_by",
        "Changes requested by an approver",
    )
    REVISION_LOCKED = "revision_locked", "Design revision locked as the approved design"
    STAGE_CHANGED = "stage_changed", "Stage changed"
    STAGE_OVERRIDDEN = "stage_overridden", "Stage overridden"
    DESIGN_REOPENED = "design_reopened", "Design reopened"
    DOCUMENT_UPLOADED = "document_uploaded", "Document uploaded"
    REMINDER_SENT = "reminder_sent", "Reminder sent"
    OVERDUE_ALERT_SENT = "overdue_alert_sent", "Overdue alert sent"
    USER_LOGIN = "user_login", "User signed in"
    SETTINGS_CHANGED = "settings_changed", "Settings changed"


class AppendOnlyError(Exception):
    """Raised when code tries to change or delete an activity log entry."""


class ActivityLogQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise AppendOnlyError("The activity log is append-only: entries cannot be changed.")

    def delete(self):
        raise AppendOnlyError("The activity log is append-only: entries cannot be deleted.")


class ActivityLog(models.Model):
    """Append-only record of who did what and when."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="activities",
        help_text="Empty for actions of the system (for example reminders).",
    )
    project = models.ForeignKey(
        "projects.Project",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="activities",
    )
    action = models.CharField(max_length=40, choices=ActivityAction.choices)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    objects = ActivityLogQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "activity log entry"
        verbose_name_plural = "activity log"
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self):
        who = self.actor.full_name if self.actor_id else "System"
        return f"{who}: {self.get_action_display()}"

    def save(self, *args, **kwargs):
        if self.pk is not None and not self._state.adding:
            raise AppendOnlyError("The activity log is append-only: entries cannot be changed.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AppendOnlyError("The activity log is append-only: entries cannot be deleted.")
