from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.choices import DecisionChannel
from apps.core.files import quotation_upload_path
from apps.core.models import TimeStampedModel


class QuotationStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    ACCEPTED = "accepted", "Accepted"
    RETURNED = "returned", "Returned"
    SUPERSEDED = "superseded", "Superseded"


# Fields that can no longer change once a quotation is accepted.
IMMUTABLE_WHEN_ACCEPTED = ("project_id", "version_no", "amount", "file")


class Quotation(TimeStampedModel):
    """One version of the quotation of a project (v1, v2, ...).

    FabriSee manages versions and decisions; it does not compute costs. Accepting a
    quotation moves the project to Design (PR3); a returned quotation needs a new version.
    """

    project = models.ForeignKey(
        "projects.Project", on_delete=models.PROTECT, related_name="quotations"
    )
    version_no = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Philippine pesos
    file = models.FileField(upload_to=quotation_upload_path, max_length=255)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=QuotationStatus.choices, default=QuotationStatus.DRAFT
    )
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="prepared_quotations"
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    # The designated approver who decided (or on whose behalf staff recorded the decision).
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="decided_quotations",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    client_comment = models.TextField(blank=True)
    decided_on_behalf = models.BooleanField(default=False)
    decision_channel = models.CharField(max_length=20, choices=DecisionChannel.choices, blank=True)
    # The staff member who recorded a decision made outside the portal.
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
    last_reminded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["project_id", "-version_no"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "version_no"], name="unique_quotation_version_per_project"
            ),
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(status="sent"),
                name="one_sent_quotation_per_project",
            ),
        ]

    def __str__(self):
        return f"{self.project.project_number} quotation v{self.version_no}"

    @property
    def label(self) -> str:
        return f"v{self.version_no}"

    @property
    def was_sent(self) -> bool:
        """True once the client could see this version (clients never see drafts)."""
        return self.sent_at is not None

    def save(self, *args, **kwargs):
        if self.pk:
            stored = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("status", *IMMUTABLE_WHEN_ACCEPTED)
                .first()
            )
            if stored and stored["status"] == QuotationStatus.ACCEPTED:
                current = {
                    "project_id": self.project_id,
                    "version_no": self.version_no,
                    "amount": self.amount,
                    "file": self.file.name,
                }
                changed = [
                    name for name in IMMUTABLE_WHEN_ACCEPTED if stored[name] != current[name]
                ]
                if changed:
                    raise models.ProtectedError(
                        "An accepted quotation cannot be changed. Create a new version instead.",
                        [self],
                    )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise models.ProtectedError(
            "Quotations are part of the project history and cannot be deleted.", [self]
        )
