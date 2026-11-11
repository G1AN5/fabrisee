import factory

from apps.accounts.tests.factories import StaffFactory
from apps.activity.models import ActivityAction, ActivityLog


class ActivityLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ActivityLog

    actor = factory.SubFactory(StaffFactory)
    action = ActivityAction.PROJECT_UPDATED
    details = factory.LazyFunction(dict)
