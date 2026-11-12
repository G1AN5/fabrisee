from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from apps.core.admin import NoDeleteAdminMixin

from .models import User


class FabriSeeUserCreationForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ("email", "full_name", "role", "client")


class FabriSeeUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(NoDeleteAdminMixin, BaseUserAdmin):
    form = FabriSeeUserChangeForm
    add_form = FabriSeeUserCreationForm
    ordering = ("full_name",)
    list_display = ("email", "full_name", "role", "client", "is_active", "last_login")
    list_filter = ("role", "is_active", "client")
    search_fields = ("email", "full_name")
    readonly_fields = ("last_login", "created_at", "updated_at", "privacy_acknowledged_at")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role", "client", "job_title", "phone")}),
        (
            "Access",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                "description": (
                    "The role decides what the user may do in FabriSee. “Staff status” and "
                    "“Superuser status” only control access to this admin site."
                ),
            },
        ),
        (
            "Dates",
            {"fields": ("last_login", "created_at", "updated_at", "privacy_acknowledged_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "role",
                    "client",
                    "usable_password",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
