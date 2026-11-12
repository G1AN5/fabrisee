from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationCategory, NotificationEvent, events_in_category
from .serializers import NotificationSerializer


def own_notifications(user):
    return Notification.objects.filter(user=user)


def unread_count(user) -> int:
    return own_notifications(user).filter(is_read=False).count()


class NotificationFilter(filters.FilterSet):
    unread = filters.BooleanFilter(method="filter_unread")
    event = filters.ChoiceFilter(choices=NotificationEvent.choices)
    category = filters.ChoiceFilter(choices=NotificationCategory.choices, method="filter_category")

    class Meta:
        model = Notification
        fields: list[str] = []

    def filter_unread(self, queryset, name, value):
        if value is None:
            return queryset
        return queryset.filter(is_read=not value)

    def filter_category(self, queryset, name, value):
        return queryset.filter(event__in=events_in_category(value))


class NotificationListView(ListAPIView):
    """`GET /api/notifications/`: the user's notifications, newest first.

    Filters: `unread=1`, `category` (requests, quotations, revisions, reminders, stages), `event`.
    The response also carries `unread_count` (for the notification bell).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter

    def get_queryset(self):
        return own_notifications(self.request.user).select_related("project")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.paginator.get_paginated_response(
            serializer.data, unread_count=unread_count(request.user)
        )


class NotificationReadView(APIView):
    """`POST /api/notifications/{id}/read/`: mark one notification as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int):
        notification = get_object_or_404(
            own_notifications(request.user).select_related("project"), pk=pk
        )
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return Response(
            {
                "notification": NotificationSerializer(notification).data,
                "unread_count": unread_count(request.user),
            }
        )


class NotificationReadAllView(APIView):
    """`POST /api/notifications/read-all/`: mark every notification of the user as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        marked = (
            own_notifications(request.user)
            .filter(is_read=False)
            .update(is_read=True, read_at=timezone.now())
        )
        return Response({"marked": marked, "unread_count": 0})
