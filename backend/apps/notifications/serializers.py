from rest_framework import serializers

from .models import EmailLog, Notification


class NotificationSerializer(serializers.ModelSerializer):
    event_label = serializers.CharField(source="get_event_display", read_only=True)
    project = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "event",
            "event_label",
            "title",
            "message",
            "link",
            "is_read",
            "read_at",
            "created_at",
            "project",
        )
        read_only_fields = fields

    def get_project(self, notification) -> dict | None:
        project = notification.project
        if project is None:
            return None
        return {"id": project.pk, "project_number": project.project_number, "title": project.title}


class EmailLogSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EmailLog
        fields = (
            "id",
            "to",
            "subject",
            "body_text",
            "body_html",
            "status",
            "status_label",
            "error",
            "created_at",
        )
        read_only_fields = fields
