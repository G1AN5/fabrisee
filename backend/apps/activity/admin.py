from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """The activity log is append-only: it can be read here, never edited."""

    list_display = ("created_at", "actor", "action", "project")
    list_filter = ("action",)
    search_fields = ("actor__full_name", "actor__email", "project__project_number")
    date_hierarchy = "created_at"
