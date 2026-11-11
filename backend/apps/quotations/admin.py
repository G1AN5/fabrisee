from django.contrib import admin

from apps.core.admin import NoDeleteAdminMixin

from .models import Quotation, QuotationStatus

# Decisions and status changes are made by the quotation services (PR3), never here.
HISTORY_FIELDS = (
    "project",
    "version_no",
    "status",
    "prepared_by",
    "sent_at",
    "decided_by",
    "decided_at",
    "client_comment",
    "decided_on_behalf",
    "decision_channel",
    "recorded_by",
    "last_reminded_at",
    "created_at",
    "updated_at",
)


@admin.register(Quotation)
class QuotationAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("project", "version_no", "amount", "status", "sent_at", "decided_at")
    list_filter = ("status",)
    search_fields = ("project__project_number", "project__title")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.status == QuotationStatus.ACCEPTED:
            # An accepted quotation is immutable.
            return [field.name for field in obj._meta.fields]
        return HISTORY_FIELDS
