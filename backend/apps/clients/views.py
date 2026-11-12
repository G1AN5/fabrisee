from django.db.models import Count, Q
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import Capability, require
from apps.projects.models import ProjectStatus

from .models import Client
from .serializers import ClientSerializer


def clients_with_counts():
    return Client.objects.annotate(
        project_count=Count("projects", distinct=True),
        active_project_count=Count(
            "projects", filter=Q(projects__status=ProjectStatus.ACTIVE), distinct=True
        ),
    ).order_by("company_name")


class ClientListView(ListAPIView):
    """`GET /api/clients/`: client companies (staff only)."""

    permission_classes = [IsAuthenticated, require(Capability.VIEW_CLIENTS)]
    serializer_class = ClientSerializer

    def get_queryset(self):
        queryset = clients_with_counts()
        search = self.request.query_params.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search) | Q(contact_person__icontains=search)
            )
        return queryset


class ClientDetailView(RetrieveAPIView):
    """`GET /api/clients/{id}/`: one client company (staff only)."""

    permission_classes = [IsAuthenticated, require(Capability.VIEW_CLIENTS)]
    serializer_class = ClientSerializer

    def get_queryset(self):
        return clients_with_counts()
