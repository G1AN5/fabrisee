from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Adds `created_at` and `updated_at` to a model."""

    # `default=timezone.now` (not auto_now_add) so the demo seed can write past dates.
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class QuotationDecisionMode(models.TextChoices):
    # TO CONFIRM: who decides on quotations (build guide, Appendix A). Default: any one
    # designated approver. `all_approvers` is reserved and not implemented yet.
    ANY_APPROVER = "any_approver", "Any one designated approver"
    ALL_APPROVERS = "all_approvers", "All designated approvers"


class SystemSetting(TimeStampedModel):
    """System-wide settings (a single row, edited by the administrator)."""

    SINGLETON_ID = 1

    company_name = models.CharField(max_length=200, default="Five Brothers Solutions Inc.")
    project_number_prefix = models.CharField(max_length=10, default="FS")
    # TO CONFIRM: reminder threshold for pending decisions (PR6). Default 48 hours.
    reminder_hours = models.PositiveIntegerField(default=48)
    # TO CONFIRM: upload size limit. Default 20 MB.
    max_upload_mb = models.PositiveIntegerField(default=20)
    quotation_decision_mode = models.CharField(
        max_length=20,
        choices=QuotationDecisionMode.choices,
        default=QuotationDecisionMode.ANY_APPROVER,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = "system setting"
        verbose_name_plural = "system settings"

    def __str__(self):
        return "System settings"

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_ID
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise models.ProtectedError("System settings cannot be deleted.", [self])

    @classmethod
    def load(cls) -> "SystemSetting":
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_ID)
        return obj
