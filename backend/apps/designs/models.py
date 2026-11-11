from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.choices import DecisionChannel
from apps.core.files import revision_upload_path, thumbnail_upload_path
from apps.core.models import TimeStampedModel


class RevisionStatus(models.TextChoices):
    PENDING_APPROVAL = "pending_approval", "Pending approval"
    CHANGES_REQUESTED = "changes_requested", "Changes requested"
    APPROVED = "approved", "Approved"
    SUPERSEDED = "superseded", "Superseded"


class ApprovalDecision(models.TextChoices):
    APPROVED = "approved", "Approved"
    CHANGES_REQUESTED = "changes_requested", "Changes requested"


# Fields that can no longer change once a revision is approved and locked.
IMMUTABLE_WHEN_APPROVED = ("project_id", "revision_no", "render", "spec_sheet")


class DesignRevision(TimeStampedModel):
    """A numbered design revision of a project (R1, R2, ...) (PR4).

    Earlier revisions stay in the history. When all designated approvers approve a
    revision it is locked as the approved design (PR5) and can no longer be changed.
    """

    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="revisions"
    )
    revision_no = models.PositiveIntegerField()
    render = models.FileField(upload_to=revision_upload_path, max_length=255)  # image or PDF
    spec_sheet = models.FileField(upload_to=revision_upload_path, max_length=255, blank=True)
    thumbnail = models.FileField(upload_to=thumbnail_upload_path, max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=RevisionStatus.choices, default=RevisionStatus.PENDING_APPROVAL
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_revisions"
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    locked_at = models.DateTimeField(null=True, blank=True)
    last_reminded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["project_id", "-revision_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "revision_no"], name="unique_revision_number_per_project"
            ),
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(status="pending_approval"),
                name="one_pending_revision_per_project",
            ),
        ]

    def __str__(self):
        return f"{self.project.project_number} {self.label}"

    @property
    def label(self) -> str:
        return f"R{self.revision_no}"

    @property
    def is_locked(self) -> bool:
        return self.locked_at is not None

    def save(self, *args, **kwargs):
        if self.pk:
            stored = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("status", "locked_at", *IMMUTABLE_WHEN_APPROVED)
                .first()
            )
            if stored and (stored["status"] == RevisionStatus.APPROVED or stored["locked_at"]):
                current = {
                    "project_id": self.project_id,
                    "revision_no": self.revision_no,
                    "render": self.render.name,
                    "spec_sheet": self.spec_sheet.name if self.spec_sheet else "",
                }
                changed = [
                    name for name in IMMUTABLE_WHEN_APPROVED if stored[name] != current[name]
                ]
                if changed:
                    raise models.ProtectedError(
                        "An approved design is locked and cannot be changed. "
                        "Upload a new revision instead.",
                        [self],
                    )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise models.ProtectedError(
            "Design revisions are part of the project history and cannot be deleted.", [self]
        )


class Approval(models.Model):
    """The decision of one designated approver on one design revision (PR5)."""

    revision = models.ForeignKey(DesignRevision, on_delete=models.PROTECT, related_name="approvals")
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approvals"
    )
    decision = models.CharField(max_length=20, choices=ApprovalDecision.choices)
    comment = models.TextField(blank=True)
    decided_on_behalf = models.BooleanField(default=False)
    decision_channel = models.CharField(
        max_length=20, choices=DecisionChannel.choices, default=DecisionChannel.PORTAL
    )
    # The staff member who recorded a decision made outside the portal.
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "approver"], name="one_decision_per_approver_per_revision"
            ),
            models.CheckConstraint(
                condition=Q(decision="approved") | ~Q(comment=""),
                name="approval_comment_required_for_changes",
                violation_error_message="A comment is required when changes are requested.",
            ),
        ]

    def __str__(self):
        return f"{self.approver.full_name}: {self.get_decision_display()} ({self.revision})"

    def delete(self, *args, **kwargs):
        raise models.ProtectedError(
            "Approvals are part of the project history and cannot be deleted.", [self]
        )
