from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.accounts.models import Role
from apps.core.files import document_upload_path, thumbnail_upload_path
from apps.core.models import TimeStampedModel


class ProjectType(models.TextChoices):
    # TO CONFIRM: the list of project types (build guide, Appendix A).
    STORE_INTERIOR = "store_interior", "Store interior"
    DISPLAY_STAND = "display_stand", "Display stand"
    BRAND_SIGN = "brand_sign", "Brand sign"
    EVENT_BOOTH = "event_booth", "Event booth"
    OTHER = "other", "Other"


class Stage(models.TextChoices):
    """Project stages, in order."""

    REQUEST = "request", "Request"
    DESIGN = "design", "Design"
    PRODUCTION = "production", "Production"
    DELIVERY_INSTALLATION = "delivery_installation", "Delivery and Installation"
    TURNOVER = "turnover", "Turnover"


STAGE_ORDER: list[str] = [stage.value for stage in Stage]


def stage_index(stage: str) -> int:
    return STAGE_ORDER.index(stage)


class ProjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ON_HOLD = "on_hold", "On hold"
    CANCELLED = "cancelled", "Cancelled"
    COMPLETED = "completed", "Completed"


class StageUpdateSource(models.TextChoices):
    RULE = "rule", "Process rule"
    MANUAL = "manual", "Recorded by staff"
    OVERRIDE = "override", "Administrator override"


class DocumentType(models.TextChoices):
    REFERENCE = "reference", "Reference file"
    QUOTATION = "quotation", "Quotation"
    RENDER = "render", "Render"
    SPEC_SHEET = "spec_sheet", "Spec sheet"
    TURNOVER = "turnover", "Turnover document"
    OTHER = "other", "Other"


class ProjectSequence(models.Model):
    """The last project number issued in a year (see `numbering.next_project_number`)."""

    year = models.PositiveIntegerField(unique=True)
    last_number = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.year}: {self.last_number}"


class Project(TimeStampedModel):
    """A commercial display project, from the client's request to turnover."""

    project_number = models.CharField(max_length=30, unique=True, editable=False)
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="projects")
    title = models.CharField(max_length=200)
    project_type = models.CharField(max_length=30, choices=ProjectType.choices)
    location = models.CharField(max_length=255)
    target_date = models.DateField()
    dimensions = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    # Changes into Design and Production happen only through PR3 and PR5 (services).
    stage = models.CharField(max_length=30, choices=Stage.choices, default=Stage.REQUEST)
    status = models.CharField(
        max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.ACTIVE
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="managed_projects",
        limit_choices_to={"role__in": [Role.PROJECT_MANAGER, Role.ADMIN]},
    )
    designer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="design_projects",
        limit_choices_to={"role": Role.DESIGNER},
    )
    # PR8: a change was requested after approval; production waits for a new approved
    # revision and, if the cost changes, a newly accepted quotation.
    design_reopened = models.BooleanField(default=False)
    requires_requote = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_projects"
    )
    approvers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectApprover",
        related_name="approver_projects",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["stage", "status"]),
            models.Index(fields=["target_date"]),
        ]

    def __str__(self):
        return f"{self.project_number} {self.title}"

    def clean(self):
        super().clean()
        if self.manager_id and self.manager.role not in (Role.PROJECT_MANAGER, Role.ADMIN):
            raise ValidationError(
                {"manager": "The manager must be a project manager or an administrator."}
            )
        if self.designer_id and self.designer.role != Role.DESIGNER:
            raise ValidationError({"designer": "Choose a user with the designer role."})

    @property
    def is_open(self) -> bool:
        """Still being worked on (not completed, cancelled, or on hold)."""
        return self.status == ProjectStatus.ACTIVE

    def is_overdue(self, today=None) -> bool:
        today = today or timezone.localdate()
        return self.status in (ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD) and (
            self.target_date < today
        )


class ProjectApprover(TimeStampedModel):
    """A client user designated to decide on the quotations and revisions of a project."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="approver_links")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="approver_links"
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="unique_project_approver"),
        ]

    def __str__(self):
        return f"{self.user.full_name} approves {self.project.project_number}"

    def clean(self):
        super().clean()
        user = self.user
        if (
            not user.is_active
            or user.role != Role.CLIENT
            or user.client_id != self.project.client_id
        ):
            raise ValidationError(
                {"user": "A designated approver must be an active user of the project's client."}
            )


class StageUpdate(models.Model):
    """One stage change of a project, with who made it and when (PR7).

    Written for every change, including the ones made by rules (PR3, PR5, PR8). Never
    edited or deleted.
    """

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="stage_updates")
    # Empty for the first entry (the project was created in the Request stage).
    from_stage = models.CharField(max_length=30, choices=Stage.choices, blank=True)
    to_stage = models.CharField(max_length=30, choices=Stage.choices)
    remarks = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="stage_updates",
    )
    source = models.CharField(
        max_length=10, choices=StageUpdateSource.choices, default=StageUpdateSource.MANUAL
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        origin = self.get_from_stage_display() if self.from_stage else "New project"
        return f"{self.project.project_number}: {origin} → {self.get_to_stage_display()}"


class Document(TimeStampedModel):
    """A file in the project document repository."""

    project = models.ForeignKey(Project, on_delete=models.PROTECT, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file = models.FileField(upload_to=document_upload_path, max_length=255)
    original_name = models.CharField(max_length=255)
    size_bytes = models.PositiveBigIntegerField(default=0)
    content_type = models.CharField(max_length=100)
    thumbnail = models.FileField(upload_to=thumbnail_upload_path, max_length=255, blank=True)
    # Staff-only documents never reach the client portal (PR9).
    visible_to_client = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_documents"
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.original_name} ({self.project.project_number})"
