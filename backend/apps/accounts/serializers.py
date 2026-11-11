from rest_framework import serializers

from .models import User
from .permissions import permissions_payload


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "Enter your email address.",
            "blank": "Enter your email address.",
            "invalid": "Enter a valid email address.",
        }
    )
    password = serializers.CharField(
        trim_whitespace=False,
        error_messages={"required": "Enter your password.", "blank": "Enter your password."},
    )


class UserBriefSerializer(serializers.ModelSerializer):
    """The few fields shown next to a person's name across the app."""

    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ("id", "full_name", "short_name", "initials", "role", "role_label", "job_title")
        read_only_fields = fields


class ContactSerializer(UserBriefSerializer):
    """A person with contact details (designated approvers, the project manager)."""

    class Meta(UserBriefSerializer.Meta):
        fields = (*UserBriefSerializer.Meta.fields, "email", "phone")
        read_only_fields = fields


class CurrentUserSerializer(serializers.ModelSerializer):
    """`GET /api/auth/me/`: the signed-in user, their role, and what they may do."""

    role_label = serializers.CharField(source="get_role_display", read_only=True)
    client = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    is_company_staff = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "short_name",
            "initials",
            "role",
            "role_label",
            "job_title",
            "phone",
            "client",
            "is_company_staff",
            "home_path",
            "privacy_acknowledged_at",
            "permissions",
        )
        read_only_fields = fields

    def get_client(self, user) -> dict | None:
        if user.client_id is None:
            return None
        return {"id": user.client_id, "company_name": user.client.company_name}

    def get_permissions(self, user) -> dict[str, bool]:
        return permissions_payload(user)
