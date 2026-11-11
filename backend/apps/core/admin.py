from django.contrib import admin

from .models import SystemSetting


class ReadOnlyAdminMixin:
    """History records can be viewed in the admin site but never added, changed, or deleted."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class NoDeleteAdminMixin:
    """Records that are deactivated instead of deleted (clients, users, projects)."""

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemSetting)
class SystemSettingAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "company_name",
        "project_number_prefix",
        "reminder_hours",
        "max_upload_mb",
        "quotation_decision_mode",
        "updated_at",
    )
    readonly_fields = ("updated_by", "created_at", "updated_at")

    def has_add_permission(self, request):
        return not SystemSetting.objects.exists()

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
