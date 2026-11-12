import factory

from apps.accounts.tests.factories import UserFactory
from apps.notifications.models import EmailLog, Notification, NotificationEvent


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(UserFactory)
    event = NotificationEvent.STAGE_CHANGED
    title = "The project moved to Production"
    message = "Your display is being built."
    link = "/portal/projects/1"


class EmailLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmailLog

    to = factory.Sequence(lambda n: f"recipient{n + 1}@example.test")
    subject = "[FabriSee] Sample message"
    body_text = "Hello."
