from django.contrib import admin

from apps.core.admin import NoDeleteAdminMixin, ReadOnlyAdminMixin

from .models import Document, Project, ProjectApprover, ProjectSequence, StageUpdate


class ProjectApproverInline(admin.TabularInline):
    model = ProjectApprover
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at",)


class StageUpdateInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = StageUpdate
    extra = 0
    fields = ("created_at", "from_stage", "to_stage", "source", "updated_by", "remarks")
    readonly_fields = fields
    ordering = ("created_at",)


@admin.register(Project)
class ProjectAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    """Projects are created by the request service (PR2) and never deleted.

    The stage is read-only here: it changes only through the process rules or the
    administrator override with a reason (services).
    """

    list_display = (
        "project_number",
        "title",
        "client",
        "project_type",
        "stage",
        "status",
        "target_date",
        "manager",
    )
    list_filter = ("stage", "status", "project_type", "client")
    search_fields = ("project_number", "title", "client__company_name")
    date_hierarchy = "created_at"
    autocomplete_fields = ("client", "manager", "designer")
    readonly_fields = (
        "project_number",
        "stage",
        "design_reopened",
        "requires_requote",
        "created_by",
        "created_at",
        "updated_at",
    )
    inlines = (ProjectApproverInline, StageUpdateInline)

    def has_add_permission(self, request):
        return False


@admin.register(StageUpdate)
class StageUpdateAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("created_at", "project", "from_stage", "to_stage", "source", "updated_by")
    list_filter = ("to_stage", "source")
    search_fields = ("project__project_number", "project__title", "remarks")
    date_hierarchy = "created_at"


@admin.register(Document)
class DocumentAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "original_name",
        "project",
        "doc_type",
        "visible_to_client",
        "size_bytes",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("doc_type", "visible_to_client")
    search_fields = ("original_name", "project__project_number", "project__title")
    readonly_fields = (
        "project",
        "file",
        "original_name",
        "size_bytes",
        "content_type",
        "thumbnail",
        "uploaded_by",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(ProjectSequence)
class ProjectSequenceAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("year", "last_number")
