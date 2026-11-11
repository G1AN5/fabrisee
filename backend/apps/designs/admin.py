from django.contrib import admin

from apps.core.admin import NoDeleteAdminMixin, ReadOnlyAdminMixin

from .models import Approval, DesignRevision

# Decisions, locking and status changes are made by the design services (PR4, PR5).
HISTORY_FIELDS = (
    "project",
    "revision_no",
    "status",
    "thumbnail",
    "uploaded_by",
    "uploaded_at",
    "locked_at",
    "last_reminded_at",
    "created_at",
    "updated_at",
)


class ApprovalInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = Approval
    extra = 0
    fields = (
        "created_at",
        "approver",
        "decision",
        "comment",
        "decided_on_behalf",
        "decision_channel",
        "recorded_by",
    )
    readonly_fields = fields


@admin.register(DesignRevision)
class DesignRevisionAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("project", "revision_no", "status", "uploaded_by", "uploaded_at", "locked_at")
    list_filter = ("status",)
    search_fields = ("project__project_number", "project__title")
    date_hierarchy = "uploaded_at"
    inlines = (ApprovalInline,)

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.is_locked:
            # The approved design is locked: nothing can be changed.
            return [field.name for field in obj._meta.fields]
        return HISTORY_FIELDS


@admin.register(Approval)
class ApprovalAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("created_at", "revision", "approver", "decision", "decided_on_behalf")
    list_filter = ("decision", "decided_on_behalf", "decision_channel")
    search_fields = ("revision__project__project_number", "approver__full_name", "comment")
    date_hierarchy = "created_at"
