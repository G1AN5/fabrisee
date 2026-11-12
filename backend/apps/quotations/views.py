from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import Capability, require
from apps.projects.presenters import present_quotation
from apps.projects.selectors import ProjectState
from apps.projects.views import visible_project


class ProjectQuotationsView(APIView):
    """`GET /api/projects/{id}/quotations/`: the quotation versions, newest first.

    Clients receive only the versions that were sent to them. Production staff have no
    access to quotations.
    """

    permission_classes = [IsAuthenticated, require(Capability.VIEW_QUOTATIONS)]

    def get(self, request, pk: int):
        state = ProjectState.of(visible_project(request.user, pk))
        quotations = state.visible_quotations(request.user)
        return Response([present_quotation(quotation, state) for quotation in quotations])
