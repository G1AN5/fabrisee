from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Role
from apps.accounts.permissions import Capability, require
from apps.projects.presenters import present_revision
from apps.projects.selectors import ProjectState
from apps.projects.views import visible_project

from .models import RevisionStatus


class ProjectRevisionsView(APIView):
    """`GET /api/projects/{id}/revisions/`: the design revisions with their approvals.

    Newest first. Production staff get the approved design first, then the history, and
    never a revision that still waits for approval.
    """

    permission_classes = [IsAuthenticated, require(Capability.VIEW_REVISIONS)]

    def get(self, request, pk: int):
        state = ProjectState.of(visible_project(request.user, pk))
        revisions = state.visible_revisions(request.user)
        if request.user.role == Role.PRODUCTION:
            revisions = sorted(
                revisions,
                key=lambda revision: (
                    revision.status != RevisionStatus.APPROVED,
                    -revision.revision_no,
                ),
            )
        return Response([present_revision(revision, state) for revision in revisions])
