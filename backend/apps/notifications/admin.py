from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import EmailLog, Notification


@admin.register(Notification)
class NotificationAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("created_at", "user", "event", "title", "project", "is_read")
    list_filter = ("event", "is_read")
    search_fields = ("title", "message", "user__email", "project__project_number")
    date_hierarchy = "created_at"


@admin.register(EmailLog)
class EmailLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("created_at", "to", "subject", "status")
    list_filter = ("status",)
    search_fields = ("to", "subject", "body_text")
    date_hierarchy = "created_at"
