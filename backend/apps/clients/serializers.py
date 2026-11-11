from rest_framework import serializers

from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """A client as staff see it (includes the staff-only notes; never used for clients)."""

    project_count = serializers.IntegerField(read_only=True)
    active_project_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Client
        fields = (
            "id",
            "company_name",
            "contact_person",
            "email",
            "phone",
            "address",
            "notes",
            "is_active",
            "project_count",
            "active_project_count",
            "created_at",
        )
        read_only_fields = fields
