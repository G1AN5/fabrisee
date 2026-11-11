from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import Capability, require
from apps.activity.models import ActivityLog
from apps.activity.services import CLIENT_VISIBLE_ACTIONS
from apps.core.files import PDF_MIME_TYPE, guess_content_type
from apps.designs.selectors import scoped_revisions
from apps.quotations.selectors import scoped_quotations

from .dashboard import build_dashboard
from .filters import ProjectFilter
from .presenters import (
    present_activity,
    present_document,
    present_pending_decision,
    present_project_card,
    present_project_detail,
    present_stage_update,
)
from .selectors import (
    ProjectState,
    pending_decisions,
    scoped_documents,
    scoped_projects,
    with_last_activity,
    with_related,
)

ORDERINGS = {
    "target_date": ("target_date", "id"),
    "-target_date": ("-target_date", "-id"),
    "last_activity": ("last_activity_at", "id"),
    "-last_activity": ("-last_activity_at", "-id"),
    "created": ("created_at", "id"),
    "-created": ("-created_at", "-id"),
    "project_number": ("project_number",),
    "-project_number": ("-project_number",),
}
DEFAULT_ORDERING = "-last_activity"


def visible_project(user, pk: int):
    """The project with everything the read side needs, or 404 if `user` may not see it.

    A project of another client answers 404, not 403, so its existence is not revealed.
    """
    queryset = with_related(with_last_activity(scoped_projects(user)))
    return get_object_or_404(queryset, pk=pk)


class ProjectListView(GenericAPIView):
    """`GET /api/projects/`: the projects the user may see, with filters and search."""

    permission_classes = [IsAuthenticated]
    filterset_class = ProjectFilter

    def get_queryset(self):
        return with_last_activity(scoped_projects(self.request.user))

    def get(self, request):
        now = timezone.now()
        queryset = self.filter_queryset(self.get_queryset())
        ordering = ORDERINGS.get(request.query_params.get("ordering", ""))
        queryset = queryset.order_by(*(ordering or ORDERINGS[DEFAULT_ORDERING]))
        page = self.paginate_queryset(with_related(queryset))
        cards = [
            present_project_card(ProjectState.of(project), request.user, now) for project in page
        ]
        return self.get_paginated_response(cards)


class ProjectDetailView(APIView):
    """`GET /api/projects/{id}/`: one project with its next step and current records."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        project = visible_project(request.user, pk)
        document_count = scoped_documents(request.user).filter(project=project).count()
        return Response(
            present_project_detail(
                ProjectState.of(project), request.user, document_count=document_count
            )
        )


class ProjectTimelineView(APIView):
    """`GET /api/projects/{id}/timeline/`: stage updates and activity of the project."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        user = request.user
        project = visible_project(user, pk)
        state = ProjectState.of(project)
        activity = ActivityLog.objects.filter(project=project).select_related("actor")
        if user.is_client_user:
            # Clients see the plain progress of their project, not internal steps.
            activity = activity.filter(action__in=CLIENT_VISIBLE_ACTIONS)
        return Response(
            {
                "stage_updates": [
                    present_stage_update(update, user) for update in state.stage_updates
                ],
                "activity": [
                    present_activity(entry) for entry in activity.order_by("-created_at", "-id")
                ],
            }
        )


class ProjectDocumentsView(APIView):
    """`GET /api/projects/{id}/documents/`: the project document repository."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int):
        project = visible_project(request.user, pk)
        documents = (
            scoped_documents(request.user)
            .filter(project=project)
            .select_related("uploaded_by")
            .order_by("-created_at", "-id")
        )
        return Response([present_document(document) for document in documents])


class DashboardView(APIView):
    """`GET /api/dashboard/`: the management dashboard (staff)."""

    permission_classes = [IsAuthenticated, require(Capability.VIEW_DASHBOARD)]

    def get(self, request):
        return Response(build_dashboard(request.user))


class PendingApprovalsView(APIView):
    """`GET /api/approvals/pending/`: every quotation and revision waiting for a decision."""

    permission_classes = [IsAuthenticated, require(Capability.VIEW_APPROVALS)]

    def get(self, request):
        now = timezone.now()
        decisions = pending_decisions(request.user, now)
        return Response(
            {
                "count": len(decisions),
                "overdue_count": sum(1 for decision in decisions if decision.is_overdue),
                "results": [
                    present_pending_decision(decision, request.user, now) for decision in decisions
                ],
            }
        )


@method_decorator(xframe_options_sameorigin, name="dispatch")
class FileDownloadView(APIView):
    """`GET /api/files/{kind}/{id}/`: the only way to read an uploaded file.

    Kinds: `document`, `quotation`, `render`, `spec`. `?inline=1` shows the file in the
    browser instead of downloading it; `?variant=thumb` returns the small preview image of
    a document or a render. Every request is checked against what the user may see (PR9).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, kind: str, pk: int):
        user = request.user
        thumbnail = request.query_params.get("variant") == "thumb"

        if kind == "document":
            document = get_object_or_404(scoped_documents(user), pk=pk)
            field = document.thumbnail if thumbnail else document.file
            name, content_type = document.original_name, document.content_type
        elif kind == "quotation":
            quotation = get_object_or_404(scoped_quotations(user).select_related("project"), pk=pk)
            field = quotation.file
            name = f"{quotation.project.project_number}-quotation-{quotation.label}.pdf"
            content_type = PDF_MIME_TYPE
        elif kind in ("render", "spec"):
            revision = get_object_or_404(scoped_revisions(user).select_related("project"), pk=pk)
            prefix = f"{revision.project.project_number}-{revision.label}"
            if kind == "spec":
                field, stem = revision.spec_sheet, f"{prefix}-spec-sheet"
            else:
                field = revision.thumbnail if thumbnail else revision.render
                stem = f"{prefix}-render"
            extension = field.name[field.name.rfind(".") :] if field and "." in field.name else ""
            name, content_type = f"{stem}{extension}", guess_content_type(field.name or "")
        else:
            raise NotFound("This kind of file does not exist.")

        if not field:
            raise NotFound("This file does not exist.")
        if thumbnail:
            name, content_type = "thumbnail.webp", "image/webp"
        try:
            handle = field.open("rb")
        except FileNotFoundError as error:
            raise NotFound("This file is missing from storage.") from error

        inline = request.query_params.get("inline") == "1" or thumbnail
        response = FileResponse(
            handle, as_attachment=not inline, filename=name, content_type=content_type
        )
        # Uploaded files never change (a new upload is a new revision or document).
        response["Cache-Control"] = "private, max-age=3600"
        return response
