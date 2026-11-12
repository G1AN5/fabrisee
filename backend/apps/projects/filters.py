from datetime import timedelta

import django_filters
from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as filters

from .models import Project, ProjectStatus, ProjectType, Stage
from .selectors import ids_needing_action, ids_waiting_on_client, overdue_filter


class ProjectFilter(filters.FilterSet):
    """Filters of `GET /api/projects/`."""

    stage = filters.ChoiceFilter(choices=Stage.choices)
    status = filters.ChoiceFilter(choices=ProjectStatus.choices)
    project_type = filters.ChoiceFilter(choices=ProjectType.choices)
    client = filters.NumberFilter(field_name="client_id")
    # Project number, title, or client name.
    q = filters.CharFilter(method="search")
    # Projects where the signed-in user is expected to act now.
    needs_action = filters.BooleanFilter(method="filter_needs_action")
    # Projects with a quotation or revision waiting for a client decision.
    waiting_on = filters.ChoiceFilter(choices=[("client", "Client")], method="filter_waiting_on")
    # Past the target date, or a decision pending longer than the reminder threshold.
    overdue = filters.BooleanFilter(method="filter_overdue")
    # Active projects with a target date within the next N days.
    due_within = django_filters.NumberFilter(method="filter_due_within")

    class Meta:
        model = Project
        fields: list[str] = []

    def search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(project_number__icontains=value)
            | Q(title__icontains=value)
            | Q(client__company_name__icontains=value)
        )

    def filter_needs_action(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(pk__in=ids_needing_action(self.request.user))

    def filter_waiting_on(self, queryset, name, value):
        if value != "client":
            return queryset
        return queryset.filter(pk__in=ids_waiting_on_client(self.request.user))

    def filter_overdue(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(overdue_filter(self.request.user))

    def filter_due_within(self, queryset, name, value):
        if value is None or value < 0:
            return queryset
        today = timezone.localdate()
        return queryset.filter(
            status=ProjectStatus.ACTIVE,
            target_date__gte=today,
            target_date__lte=today + timedelta(days=int(value)),
        )
